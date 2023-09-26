# Create your views here.
import io
# Create your views here.
import json
import logging
from dataclasses import asdict
from typing import List

import arrow
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.utils.decorators import method_decorator
from rest_framework import generics, mixins, status
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser
from shapely.geometry import shape

from auth_helper.utils import requires_scopes
from geo_fence_operations import rtree_geo_fence_helper
from geo_fence_operations.models import GeoFence
from security import signing

from .data_definitions import FlightDeclarationCreateResponse
from .flight_declarations_rtree_helper import \
    FlightDeclarationRTreeIndexFactory
from .models import FlightDeclaration
from .pagination import StandardResultsSetPagination
from .serializers import (FlightDeclarationApprovalSerializer,
                          FlightDeclarationRequestSerializer,
                          FlightDeclarationSerializer,
                          FlightDeclarationStateSerializer)
from .tasks import (send_operational_update_message,
                    submit_flight_declaration_to_dss)
from .utils import OperationalIntentsConverter

logger = logging.getLogger("django")


def _parse_flight_declaration_request(json_payload):
    """
    Validate the JSON payload to make sure all required fields are provided and the flight times are in proper order
    """
    error = None
    fd_request = None
    serializer = FlightDeclarationRequestSerializer(data=json_payload)
    if not serializer.is_valid():
        error = serializer.errors
        return fd_request, error

    fd_request = serializer.create(serializer.validated_data)

    # Validate flight time fields
    now = arrow.now()
    try:
        fd_request.start_datetime = (
            now.isoformat()
            if fd_request.start_datetime is None
            else arrow.get(fd_request.start_datetime).isoformat()
        )
        fd_request.end_datetime = (
            now.isoformat()
            if fd_request.end_datetime is None
            else arrow.get(fd_request.end_datetime).isoformat()
        )
    except Exception:
        ten_mins_from_now = now.shift(minutes=10)
        fd_request.start_datetime = now.isoformat()
        fd_request.end_datetime = ten_mins_from_now.isoformat()

    two_days_from_now = now.shift(days=2)

    # verify start and end date time
    s_datetime = arrow.get(fd_request.start_datetime)
    e_datetime = arrow.get(fd_request.end_datetime)
    if (
        s_datetime < now
        or e_datetime < now
        or e_datetime > two_days_from_now
        or s_datetime > two_days_from_now
    ):
        error = {
            "message": "A flight declaration cannot have a start or end time in the past or after two days from current time."
        }

    # Validate GeoJSON
    all_features = []  # TODO Do we need this all_features?
    for feature in fd_request.flight_declaration_geo_json["features"]:
        geometry = feature["geometry"]
        s = shape(geometry)
        if s.is_valid:
            all_features.append(s)
        else:
            error = {
                "message": "Error in processing the submitted GeoJSON: every Feature in a GeoJSON FeatureCollection must have a valid geometry, please check your submitted FeatureCollection"
            }
        props = feature["properties"]
        try:
            assert "min_altitude" in props
            assert "max_altitude" in props
        except AssertionError:
            error = {
                "message": "Error in processing the submitted GeoJSON: every Feature in a GeoJSON FeatureCollection must have a min_altitude and max_altitude data structure"
            }

    return fd_request, error


def _get_operational_intent(fd_request):
    is_approved = False  # Default accepted is False
    my_operational_intent_converter = OperationalIntentsConverter()
    partial_op_int_ref = (
        my_operational_intent_converter.create_partial_operational_intent_ref(
            geo_json_fc=fd_request.flight_declaration_geo_json,
            start_datetime=fd_request.start_datetime,
            end_datetime=fd_request.end_datetime,
            priority=0,
        )
    )
    bounds = my_operational_intent_converter.get_geo_json_bounds()
    logging.info("Checking intersections with Geofences..")

    view_box = [float(i) for i in bounds.split(",")]
    fence_within_timelimits = GeoFence.objects.filter(
        start_datetime__lte=fd_request.start_datetime,
        end_datetime__gte=fd_request.end_datetime,
    ).exists()

    all_relevant_fences = []
    if fence_within_timelimits:
        all_fences_within_timelimits = GeoFence.objects.filter(
            start_datetime__lte=fd_request.start_datetime,
            end_datetime__gte=fd_request.end_datetime,
        )
        INDEX_NAME = "geofence_idx"
        my_rtree_helper = rtree_geo_fence_helper.GeoFenceRTreeIndexFactory(
            index_name=INDEX_NAME
        )
        my_rtree_helper.generate_geo_fence_index(
            all_fences=all_fences_within_timelimits
        )
        all_relevant_fences = my_rtree_helper.check_box_intersection(view_box=view_box)
        relevant_id_set = []
        for i in all_relevant_fences:
            relevant_id_set.append(i["geo_fence_id"])

        my_rtree_helper.clear_rtree_index()
        logging.info(
            "Geofence intersections checked, found {num_intersections} fences"
            % {"num_intersections": len(relevant_id_set)}
        )
        if all_relevant_fences:
            is_approved = 0

    all_relevant_declarations = []
    existing_declaration_within_timelimits = FlightDeclaration.objects.filter(
        start_datetime__lte=fd_request.start_datetime,
        end_datetime__gte=fd_request.end_datetime,
    ).exists()
    if existing_declaration_within_timelimits:
        all_declarations_within_timelimits = FlightDeclaration.objects.filter(
            start_datetime__lte=fd_request.start_datetime,
            end_datetime__gte=fd_request.end_datetime,
        )
        INDEX_NAME = "flight_declaration_idx"
        my_fd_rtree_helper = FlightDeclarationRTreeIndexFactory(index_name=INDEX_NAME)
        my_fd_rtree_helper.generate_flight_declaration_index(
            all_flight_declarations=all_declarations_within_timelimits
        )
        all_relevant_declarations = my_fd_rtree_helper.check_box_intersection(
            view_box=view_box
        )
        relevant_id_set = []
        for i in all_relevant_declarations:
            relevant_id_set.append(i["flight_declaration_id"])
        my_fd_rtree_helper.clear_rtree_index()
        logging.info(
            "Flight Declaration intersections checked, found {num_intersections} declarations"
            % {"all_relevant_declarations": len(relevant_id_set)}
        )
        if all_relevant_declarations:
            is_approved = 0

    return (
        partial_op_int_ref,
        bounds,
        all_relevant_fences,
        all_relevant_declarations,
        is_approved,
    )


def _send_fd_creation_notifications(
    flight_declaration_id: str, all_relevant_fences, all_relevant_declarations
) -> None:
    send_operational_update_message.delay(
        flight_declaration_id=flight_declaration_id,
        message_text="Flight Declaration created..",
        level="info",
    )

    if all_relevant_fences and all_relevant_declarations:
        # Async submit flight declaration to DSS
        logger.info(
            "Self deconfliction failed, this declaration cannot be sent to the DSS system.."
        )

        send_operational_update_message.delay(
            flight_declaration_id=flight_declaration_id,
            message_text="Self deconfliction failed for operation {operation_id} did not pass self-deconfliction, there are existing operations declared".format(
                operation_id=flight_declaration_id
            ),
            level="error",
        )

    else:
        logger.info(
            "Self deconfliction success, this declaration will be sent to the DSS system, if a DSS URL is provided.."
        )
        submit_flight_declaration_to_dss.delay(
            flight_declaration_id=flight_declaration_id
        )
    return None


@api_view(["POST"])
@requires_scopes(["blender.write"])
def set_flight_declaration(request: HttpRequest):
    """
    Add a new Flight Declaration. Submit a Flight Declaration into Flight Blender.
    """
    try:
        assert request.headers["Content-Type"] == "application/json"
    except AssertionError:
        msg = {"message": "Unsupported Media Type"}
        return HttpResponse(
            json.dumps(msg),
            status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            content_type="application/json",
        )

    stream = io.BytesIO(request.body)
    json_payload = JSONParser().parse(stream)

    # Validate the JSON payload
    parsed_fd_request, parse_error = _parse_flight_declaration_request(json_payload)

    if parse_error:
        return HttpResponse(
            json.dumps(parse_error),
            status=status.HTTP_400_BAD_REQUEST,
            content_type="application/json",
        )

    default_state = 1  # Default state is Accepted
    (
        partial_op_int_ref,
        bounds,
        all_relevant_fences,
        all_relevant_declarations,
        is_approved,
    ) = _get_operational_intent(parsed_fd_request)

    fo = FlightDeclaration(
        operational_intent=json.loads(json.dumps(asdict(partial_op_int_ref))),
        bounds=bounds,
        type_of_operation=parsed_fd_request.type_of_operation,
        submitted_by=parsed_fd_request.submitted_by,
        is_approved=is_approved,
        start_datetime=parsed_fd_request.start_datetime,
        end_datetime=parsed_fd_request.end_datetime,
        originating_party=parsed_fd_request.originating_party,
        flight_declaration_raw_geojson=json.dumps(
            parsed_fd_request.flight_declaration_geo_json
        ),
        state=default_state,
    )
    fo.save()

    # Send flight creation notifications
    flight_declaration_id = str(fo.id)
    _send_fd_creation_notifications(
        flight_declaration_id, all_relevant_fences, all_relevant_declarations
    )

    creation_response = FlightDeclarationCreateResponse(
        id=flight_declaration_id,
        message="Submitted Flight Declaration",
        is_approved=is_approved,
        state=default_state,
    )

    op = json.dumps(asdict(creation_response))
    return HttpResponse(
        op, status=status.HTTP_201_CREATED, content_type="application/json"
    )


@api_view(["POST"])
@requires_scopes(["blender.write"])
def set_signed_flight_declaration(request: HttpRequest):
    try:
        assert request.headers["Content-Type"] == "application/json"
    except AssertionError:
        msg = {"message": "Unsupported Media Type"}
        return HttpResponse(
            json.dumps(msg),
            status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            content_type="application/json",
        )

    stream = io.BytesIO(request.body)
    json_payload = JSONParser().parse(stream)

    payload_verifier = signing.MessageVerifier()
    payload_verified = payload_verifier.verify_message(request)
    if not payload_verified:
        return HttpResponse(
            json.dumps(
                {
                    "message": "Could not verify against public keys setup in Flight Blender"
                }
            ),
            status=status.HTTP_400_BAD_REQUEST,
            content_type="application/json",
        )

    # Validate the JSON payload
    parsed_fd_request, parse_error = _parse_flight_declaration_request(json_payload)

    if parse_error:
        return HttpResponse(
            json.dumps(parse_error),
            status=status.HTTP_400_BAD_REQUEST,
            content_type="application/json",
        )

    default_state = 1  # Default state is Accepted
    (
        partial_op_int_ref,
        bounds,
        all_relevant_fences,
        all_relevant_declarations,
        is_approved,
    ) = _get_operational_intent(parsed_fd_request)

    fo = FlightDeclaration(
        operational_intent=json.loads(json.dumps(asdict(partial_op_int_ref))),
        bounds=bounds,
        type_of_operation=parsed_fd_request.type_of_operation,
        submitted_by=parsed_fd_request.submitted_by,
        is_approved=is_approved,
        start_datetime=parsed_fd_request.start_datetime,
        end_datetime=parsed_fd_request.end_datetime,
        originating_party=parsed_fd_request.originating_party,
        flight_declaration_raw_geojson=json.dumps(
            parsed_fd_request.flight_declaration_geo_json
        ),
        state=default_state,
    )
    fo.save()

    # Send flight creation notifications
    flight_declaration_id = str(fo.id)
    _send_fd_creation_notifications(
        flight_declaration_id, all_relevant_fences, all_relevant_declarations
    )

    creation_response = FlightDeclarationCreateResponse(
        id=flight_declaration_id,
        message="Submitted Flight Declaration",
        is_approved=is_approved,
        state=default_state,
    )

    op = json.dumps(asdict(creation_response))

    signer = signing.ResponseSigner()
    signed_response = signer.sign_http_message_via_ietf(
        json_payload=op, original_request=request
    )
    signed_response.content = op
    signed_response.status_code = status.HTTP_201_CREATED
    return signed_response


@method_decorator(requires_scopes(["blender.write"]), name="dispatch")
class FlightDeclarationApproval(mixins.UpdateModelMixin, generics.GenericAPIView):
    queryset = FlightDeclaration.objects.all()
    serializer_class = FlightDeclarationApprovalSerializer

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


@method_decorator(requires_scopes(["blender.write"]), name="dispatch")
class FlightDeclarationStateUpdate(mixins.UpdateModelMixin, generics.GenericAPIView):
    queryset = FlightDeclaration.objects.all()
    serializer_class = FlightDeclarationStateSerializer

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


@method_decorator(requires_scopes(["blender.read"]), name="dispatch")
class FlightDeclarationDetail(mixins.RetrieveModelMixin, generics.GenericAPIView):
    queryset = FlightDeclaration.objects.all()
    serializer_class = FlightDeclarationSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


@method_decorator(requires_scopes(["blender.read"]), name="dispatch")
class FlightDeclarationList(mixins.ListModelMixin, generics.GenericAPIView):
    queryset = FlightDeclaration.objects.all()
    serializer_class = FlightDeclarationSerializer
    pagination_class = StandardResultsSetPagination

    def get_relevant_flight_declaration(
        self,
        start_date,
        end_date,
        view_port: List[float],
        max_alt: int = None,
        min_alt: int = None,
        states: List[int] = None,
    ):
        filter_query = Q()
        if start_date and end_date:
            s_date = arrow.get(start_date, "YYYY-MM-DD HH:mm:ss")
            e_date = arrow.get(end_date, "YYYY-MM-DD HH:mm:ss")

        else:
            present = arrow.now()
            s_date = present.shift(days=-1)
            e_date = present.shift(days=1)

        all_fd_overlaps_timelimits = FlightDeclaration.objects.filter(
            end_datetime__gte=s_date.isoformat(), start_datetime__lte=e_date.isoformat()
        )
        filter_query.add(
            Q(
                end_datetime__gte=s_date.isoformat(),
                start_datetime__lte=e_date.isoformat(),
            ),
            Q.AND,
        )

        logging.info("Found %s flight declarations" % len(all_fd_overlaps_timelimits))

        if view_port:
            INDEX_NAME = "opint_idx"
            my_rtree_helper = FlightDeclarationRTreeIndexFactory(index_name=INDEX_NAME)
            my_rtree_helper.generate_flight_declaration_index(
                all_flight_declarations=all_fd_overlaps_timelimits
            )

            all_relevant_fences = my_rtree_helper.check_box_intersection(
                view_box=view_port
            )
            relevant_id_set = []
            for i in all_relevant_fences:
                relevant_id_set.append(i["flight_declaration_id"])

            my_rtree_helper.clear_rtree_index()

            filter_query.add(Q(id__in=relevant_id_set), Q.AND)

        if max_alt:
            filter_query.add(
                Q(
                    operational_intent__volumes__0__volume__altitude_upper__value__lte=int(
                        max_alt
                    )
                ),
                Q.AND,
            )
        if min_alt:
            filter_query.add(
                Q(
                    operational_intent__volumes__0__volume__altitude_lower__value__gte=int(
                        min_alt
                    )
                ),
                Q.AND,
            )
        if states:
            filter_query.add(
                Q(state__in=states),
                Q.AND,
            )

        filtered = FlightDeclaration.objects.filter(filter_query)
        return filtered

    def get_queryset(self):
        start_date = self.request.query_params.get("start_date", None)
        end_date = self.request.query_params.get("end_date", None)

        max_alt = self.request.query_params.get("max_alt", None)
        min_alt = self.request.query_params.get("min_alt", None)

        view = self.request.query_params.get("view", None)
        state_str = self.request.query_params.get("states")

        states = []
        if state_str:
            states = state_str.split(",")
        view_port = []
        if view:
            view_port = [float(i) for i in view.split(",")]

        responses = self.get_relevant_flight_declaration(
            view_port=view_port,
            start_date=start_date,
            end_date=end_date,
            max_alt=max_alt,
            min_alt=min_alt,
            states=states,
        )
        return responses

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
