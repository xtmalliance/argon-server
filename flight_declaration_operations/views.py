# Create your views here.
from auth_helper.utils import requires_scopes

# Create your views here.
import json
import arrow
import logging
import io
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer
from typing import List
from django.http import HttpResponse, HttpRequest
from .models import FlightDeclaration
from dataclasses import asdict
from geo_fence_operations import rtree_geo_fence_helper
from geo_fence_operations.models import GeoFence
from .flight_declarations_rtree_helper import FlightDeclarationRTreeIndexFactory
from shapely.geometry import shape
from .data_definitions import (
    FlightDeclarationCreateResponse,
)
from rest_framework import mixins, generics
from .serializers import (
    FlightDeclarationSerializer,
    FlightDeclarationApprovalSerializer,
    FlightDeclarationStateSerializer,
    FlightDeclarationRequestSerializer,
)
from django.utils.decorators import method_decorator
from .utils import OperationalIntentsConverter
from .tasks import submit_flight_declaration_to_dss, send_operational_update_message
from .pagination import StandardResultsSetPagination
from os import environ as env

logger = logging.getLogger("django")


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
            json.dumps(msg), status=415, content_type="application/json"
        )

    stream = io.BytesIO(request.body)
    json_payload = JSONParser().parse(stream)

    serializer = FlightDeclarationRequestSerializer(data=json_payload)
    if not serializer.is_valid():
        return HttpResponse(
            JSONRenderer().render(serializer.errors),
            status=400,
            content_type="application/json",
        )

    try:
        flight_declaration_geo_json = json_payload["flight_declaration_geo_json"]
    except KeyError:
        msg = json.dumps(
            {
                "message": "A valid flight declaration as specified by the A flight declaration protocol must be submitted."
            }
        )
        return HttpResponse(msg, status=400)

    submitted_by = (
        None if "submitted_by" not in json_payload else json_payload["submitted_by"]
    )
    is_approved = False
    type_of_operation = (
        0
        if "type_of_operation" not in json_payload
        else json_payload["type_of_operation"]
    )
    originating_party = (
        "No Flight Information"
        if "originating_party" not in json_payload
        else json_payload["originating_party"]
    )
    now = arrow.now()
    try:
        start_datetime = (
            now.isoformat()
            if "start_datetime" not in json_payload
            else arrow.get(json_payload["start_datetime"]).isoformat()
        )
        end_datetime = (
            now.isoformat()
            if "end_datetime" not in json_payload
            else arrow.get(json_payload["end_datetime"]).isoformat()
        )
    except Exception:
        ten_mins_from_now = now.shift(minutes=10)
        start_datetime = now.isoformat()
        end_datetime = ten_mins_from_now.isoformat()

    two_days_from_now = now.shift(days=2)

    # verify start and end date time
    s_datetime = arrow.get(start_datetime)
    e_datetime = arrow.get(end_datetime)

    if (
        s_datetime < now
        or e_datetime < now
        or e_datetime > two_days_from_now
        or s_datetime > two_days_from_now
    ):
        msg = json.dumps(
            {
                "message": "A flight declaration cannot have a start / end time in the past or after two days from current time."
            }
        )
        return HttpResponse(msg, status=400)
    all_features = []

    for feature in flight_declaration_geo_json["features"]:
        geometry = feature["geometry"]
        s = shape(geometry)
        if s.is_valid:
            all_features.append(s)
        else:
            op = json.dumps(
                {
                    "message": "Error in processing the submitted GeoJSON: every Feature in a GeoJSON FeatureCollection must have a valid geometry, please check your submitted FeatureCollection"
                }
            )
            return HttpResponse(op, status=400, content_type="application/json")

        props = feature["properties"]
        try:
            assert "min_altitude" in props
            assert "max_altitude" in props
        except AssertionError:
            op = json.dumps(
                {
                    "message": "Error in processing the submitted GeoJSON every Feature in a GeoJSON FeatureCollection must have a min_altitude and max_altitude data structure"
                }
            )
            return HttpResponse(op, status=400, content_type="application/json")

    default_state = 1  # Default state is Accepted

    my_operational_intent_converter = OperationalIntentsConverter()

    partial_op_int_ref = (
        my_operational_intent_converter.create_partial_operational_intent_ref(
            geo_json_fc=flight_declaration_geo_json,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            priority=0,
        )
    )

    bounds = my_operational_intent_converter.get_geo_json_bounds()
    logging.info("Checking intersections with Geofences..")
    view_box = [float(i) for i in bounds.split(",")]

    fence_within_timelimits = GeoFence.objects.filter(
        start_datetime__lte=start_datetime, end_datetime__gte=end_datetime
    ).exists()
    all_relevant_fences = []
    if fence_within_timelimits:
        all_fences_within_timelimits = GeoFence.objects.filter(
            start_datetime__lte=start_datetime, end_datetime__gte=end_datetime
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
        start_datetime__lte=start_datetime, end_datetime__gte=end_datetime
    ).exists()
    if existing_declaration_within_timelimits:
        all_declarations_within_timelimits = FlightDeclaration.objects.filter(
            start_datetime__lte=start_datetime, end_datetime__gte=end_datetime
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

    fo = FlightDeclaration(
        operational_intent=json.dumps(asdict(partial_op_int_ref)),
        bounds=bounds,
        type_of_operation=type_of_operation,
        submitted_by=submitted_by,
        is_approved=is_approved,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        originating_party=originating_party,
        flight_declaration_raw_geojson=json.dumps(flight_declaration_geo_json),
        state=default_state,
    )
    fo.save()

    flight_declaration_id = str(fo.id)
    amqp_connection_url = env.get("AMQP_URL", 0)
    if amqp_connection_url:
        send_operational_update_message.delay(
            flight_declaration_id=flight_declaration_id,
            message_text="Flight Declaration created..",
            level="info",
        )

    if all_relevant_fences and all_relevant_declarations:
        # Async submic flight declaration to DSS
        logger.info(
            "Self deconfliction failed, this declaration cannot be sent to the DSS system.."
        )
        if amqp_connection_url:
            self_deconfliction_failed_msg = "Self deconfliction failed for operation {operation_id} did not pass self-deconfliction, there are existing operationd declared".format(
                operation_id=flight_declaration_id
            )
            send_operational_update_message.delay(
                flight_declaration_id=flight_declaration_id,
                message_text=self_deconfliction_failed_msg,
                level="error",
            )

    else:
        logger.info(
            "Self deconfliction success, this declaration will be sent to the DSS system, if a DSS URL is provided.."
        )
        submit_flight_declaration_to_dss.delay(
            flight_declaration_id=flight_declaration_id
        )
    creation_response = FlightDeclarationCreateResponse(
        id=flight_declaration_id,
        message="Submitted Flight Declaration",
        is_approved=is_approved,
        state=default_state,
    )

    op = json.dumps(asdict(creation_response))
    return HttpResponse(op, status=200, content_type="application/json")


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
        self, start_date, end_date, view_port: List[float]
    ):
        present = arrow.now()
        if start_date and end_date:
            s_date = arrow.get(start_date, "YYYY-MM-DD")
            e_date = arrow.get(end_date, "YYYY-MM-DD")

        else:
            s_date = present.shift(days=-1)
            e_date = present.shift(days=1)
        all_fd_within_timelimits = FlightDeclaration.objects.filter(
            start_datetime__gte=s_date.isoformat(), end_datetime__lte=e_date.isoformat()
        )

        logging.info("Found %s flight declarations" % len(all_fd_within_timelimits))
        if view_port:
            INDEX_NAME = "opint_idx"
            my_rtree_helper = FlightDeclarationRTreeIndexFactory(index_name=INDEX_NAME)
            my_rtree_helper.generate_flight_declaration_index(
                all_flight_declarations=all_fd_within_timelimits
            )

            all_relevant_fences = my_rtree_helper.check_box_intersection(
                view_box=view_port
            )
            relevant_id_set = []
            for i in all_relevant_fences:
                relevant_id_set.append(i["flight_declaration_id"])

            my_rtree_helper.clear_rtree_index()
            filtered_relevant_fd = FlightDeclaration.objects.filter(
                id__in=relevant_id_set
            )

        else:
            filtered_relevant_fd = all_fd_within_timelimits

        return filtered_relevant_fd

    def get_queryset(self):
        start_date = self.request.query_params.get("start_date", None)
        end_date = self.request.query_params.get("end_date", None)

        view = self.request.query_params.get("view", None)
        view_port = []
        if view:
            view_port = [float(i) for i in view.split(",")]

        responses = self.get_relevant_flight_declaration(
            view_port=view_port, start_date=start_date, end_date=end_date
        )
        return responses

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
