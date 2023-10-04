# Create your views here.
import io
import json
import logging
from dataclasses import asdict

from typing import List
import shapely.geometry
from django.http import JsonResponse
from django.views.generic import TemplateView
from rest_framework.decorators import api_view

from auth_helper.utils import requires_scopes
from rid_operations import view_port_ops
from rid_operations.data_definitions import (
    RIDAircraftState,
    RIDFlightDetails,
    SignedUnSignedTelemetryObservations,
)
from rid_operations.tasks import stream_rid_data_v22

from . import flight_stream_helper
from .data_definitions import (
    FlightObservationsProcessingResponse,
    SingleAirtrafficObservation,
)
from .tasks import start_openskies_stream, write_incoming_air_traffic_data

logger = logging.getLogger("django")
from os import environ as env

from django.http import HttpRequest, HttpResponse
from django.utils.decorators import method_decorator
from dotenv import find_dotenv, load_dotenv
from jwcrypto import jwk, jwt
from rest_framework import generics, status
from rest_framework.parsers import JSONParser

from encoders import DateTimeEncoder

from .models import SignedTelmetryPublicKey
from security.signing import MessageVerifier, ResponseSigner
from .rid_telemetry_helper import (
    BlenderTelemetryValidator,
    NestedDict,
    current_state_json_to_object,
    flight_detail_json_to_object,
)
from .serializers import (
    SignedTelmetryPublicKeySerializer,
    TelemetryRequest,
    TelemetryRequestSerializer,
)

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)


class HomeView(TemplateView):
    template_name = "homebase/home.html"


@api_view(["GET"])
def public_key_view(request):
    # Source: https://github.com/jazzband/django-oauth-toolkit/blob/016c6c3bf62c282991c2ce3164e8233b81e3dd4d/oauth2_provider/views/oidc.py#L105
    keys = []
    private_key = env.get("SECRET_KEY", None)

    if private_key:
        try:
            for pem in [private_key]:
                key = jwk.JWK.from_pem(pem.encode("utf8"))
                data = {"alg": "RS256", "use": "sig", "kid": key.thumbprint()}
                data.update(json.loads(key.export_public()))
                keys.append(data)

            response = JsonResponse({"keys": keys})
            response["Access-Control-Allow-Origin"] = "*"
        except:
            response = JsonResponse({})
    else:
        response = JsonResponse({})

    return response


@api_view(["GET"])
def ping(request):
    return JsonResponse({"message": "pong"}, status=200)


@api_view(['GET'])
@requires_scopes(['blender.read'])
def ping_with_auth(request):
    return JsonResponse({"message":"pong with auth"}, status=200)


@api_view(["POST"])
@requires_scopes(["blender.write"])
def set_air_traffic(request):
    """This is the main POST method that takes in a request for Air traffic observation and processes the input data"""

    try:
        assert request.headers["Content-Type"] == "application/json"
    except AssertionError:
        msg = {"message": "Unsupported Media Type"}
        return JsonResponse(msg, status=415)
    else:
        req = request.data

    try:
        observations = req["observations"]
    except KeyError as ke:
        msg = FlightObservationsProcessingResponse(
            message="At least one observation is required: observations with a list of observation objects. One or more of these were not found in your JSON request. For sample data see: https://github.com/openskies-sh/airtraffic-data-protocol-development/blob/master/Airtraffic-Data-Protocol.md#sample-traffic-object",
            status=400,
        )

        m = asdict(msg)
        return JsonResponse(m, status=m["status"])

    for observation in observations:
        try:
            lat_dd = observation["lat_dd"]
            lon_dd = observation["lon_dd"]
            altitude_mm = observation["altitude_mm"]
            traffic_source = observation["traffic_source"]
            source_type = observation["source_type"]
            icao_address = observation["icao_address"]

        except KeyError as obs_ke:
            msg = {
                "message": "One of your obervations do not have the mandatory required field"
            }
            return JsonResponse(msg, status=400)
            # logging.error("Not all data was provided")
        metadata = {}

        if "metadata" in observation.keys():
            metadata = observation["metadata"]

        so = SingleAirtrafficObservation(
            lat_dd=lat_dd,
            lon_dd=lon_dd,
            altitude_mm=altitude_mm,
            traffic_source=traffic_source,
            source_type=source_type,
            icao_address=icao_address,
            metadata=json.dumps(metadata),
        )

        msgid = write_incoming_air_traffic_data.delay(
            json.dumps(asdict(so))
        )  # Send a job to the task queue

    op = FlightObservationsProcessingResponse(message="OK", status=200)
    return JsonResponse(asdict(op), status=op.status)


@api_view(["GET"])
@requires_scopes(["blender.read"])
def get_air_traffic(request):
    """This is the end point for the rid_qualifier test DSS network call once a subscription is updated"""

    # get the view bounding box
    # get the existing subscription id , if no subscription exists, then reject

    try:
        view = request.query_params["view"]
        view_port = [float(i) for i in view.split(",")]
    except Exception as ke:
        incorrect_parameters = {
            "message": "A view bbox is necessary with four values: minx, miny, maxx and maxy"
        }
        return JsonResponse(
            json.loads(json.dumps(incorrect_parameters)),
            status=400,
            content_type="application/json",
        )

    view_port_valid = view_port_ops.check_view_port(view_port_coords=view_port)

    b = shapely.geometry.box(view_port[1], view_port[0], view_port[3], view_port[2])
    co_ordinates = list(zip(*b.exterior.coords.xy))
    # Convert bounds vertex list
    vertex_list = []
    for cur_co_ordinate in co_ordinates:
        lat_lng = {"lng": 0, "lat": 0}
        lat_lng["lng"] = cur_co_ordinate[0]
        lat_lng["lat"] = cur_co_ordinate[1]
        vertex_list.append(lat_lng)
    # remove the final point
    vertex_list.pop()

    if view_port_valid:
        stream_ops = flight_stream_helper.StreamHelperOps()
        pull_cg = stream_ops.get_pull_cg()
        all_streams_messages = pull_cg.read()

        unique_flights = []
        # Keep only the latest message
        try:
            for message in all_streams_messages:
                unique_flights.append(
                    {
                        "timestamp": message.timestamp,
                        "seq": message.sequence,
                        "msg_data": message.data,
                        "address": message.data["icao_address"],
                    }
                )
            # sort by date
            unique_flights.sort(key=lambda item: item["timestamp"], reverse=True)
            # Keep only the latest message
            distinct_messages = {
                i["address"]: i for i in reversed(unique_flights)
            }.values()

        except KeyError as ke:
            logger.error(
                "Error in sorting distinct messages, ICAO name not defined %s" % ke
            )
            distinct_messages = []
        all_traffic_observations: List[SingleAirtrafficObservation] = []
        for observation in distinct_messages:
            observation_data = observation["msg_data"]
            observation_metadata = json.loads(observation_data["metadata"])
            so = SingleAirtrafficObservation(
                lat_dd=observation_data["lat_dd"],
                lon_dd=observation_data["lon_dd"],
                altitude_mm=observation_data["altitude_mm"],
                traffic_source=observation_data["traffic_source"],
                source_type=observation_data["source_type"],
                icao_address=observation_data["icao_address"],
                metadata=observation_metadata,
            )
            all_traffic_observations.append(asdict(so))

        return JsonResponse(
            {"observations": all_traffic_observations},
            status=200,
            content_type="application/json",
        )
    else:
        view_port_error = {"message": "A incorrect view port bbox was provided"}
        return JsonResponse(
            json.loads(json.dumps(view_port_error)),
            status=400,
            content_type="application/json",
        )


@api_view(["GET"])
@requires_scopes(["blender.read"])
def start_opensky_feed(request):
    # This method takes in a view port as a lat1,lon1,lat2,lon2 co-ordinate system and for 60 seconds starts the stream of data from the OpenSky Network.

    try:
        view = request.query_params["view"]
        view_port = [float(i) for i in view.split(",")]
    except Exception as ke:
        incorrect_parameters = {
            "message": "A view bbox is necessary with four values: minx, miny, maxx and maxy"
        }

        return JsonResponse(
            json.loads(json.dumps(incorrect_parameters)),
            status=400,
            content_type="application/json",
        )

    view_port_valid = view_port_ops.check_view_port(view_port_coords=view_port)

    if view_port_valid:
        start_openskies_stream.delay(view_port=json.dumps(view_port))

        return JsonResponse(
            {"message": "Openskies Newtork stream started"},
            status=200,
            content_type="application/json",
        )
    else:
        view_port_error = {"message": "An incorrect view port bbox was provided"}

        return JsonResponse(
            json.loads(json.dumps(view_port_error)),
            status=400,
            content_type="application/json",
        )


@api_view(["PUT"])
def set_signed_telemetry(request):
    # This endpoint sets signed telemetry details into Flight Blender, use this endpoint to securly send signed telemetry information into Blender, since the messages are signed, we turn off any auth requirements for tokens and validate against allowed public keys in Blender.

    message_verifier = MessageVerifier()
    response_signer = ResponseSigner()
    verified = message_verifier.verify_message(request)

    if not verified:
        return JsonResponse(
            json.dumps(
                {
                    "message": "Could not verify against public keys of USSP client(GCS) setup in Flight Blender"
                }
            ),
            status=400,
            content_type="application/json",
        )
    else:
        raw_data = request.data
        my_telemetry_validator = BlenderTelemetryValidator()
        observations_exist = my_telemetry_validator.validate_observation_key_exists(
            raw_request_data=raw_data
        )
        if not observations_exist:
            incorrect_parameters = {
                "message": "A flight observation object with current state and flight details is necessary"
            }
            return JsonResponse(
                incorrect_parameters, status=400, content_type="application/json"
            )
        # Get a list of flight data

        raw_data = request.data

        my_telemetry_validator = BlenderTelemetryValidator()

        observations_exist = my_telemetry_validator.validate_observation_key_exists(
            raw_request_data=raw_data
        )
        if not observations_exist:
            incorrect_parameters = {
                "message": "A flight observation object with current state and flight details is necessary"
            }
            return JsonResponse(
                incorrect_parameters, status=400, content_type="application/json"
            )
        # Get a list of flight data

        rid_observations = raw_data["observations"]

        unsigned_telemetry_observations: List[SignedUnSignedTelemetryObservations] = []
        for flight in rid_observations:
            flight_details_current_states_exist = (
                my_telemetry_validator.validate_flight_details_current_states_exist(
                    flight=flight
                )
            )
            if not flight_details_current_states_exist:
                incorrect_parameters = {
                    "message": "A flights object with current states, flight details is necessary"
                }
                return JsonResponse(
                    incorrect_parameters, status=400, content_type="application/json"
                )

            current_states = flight["current_states"]
            flight_details = flight["flight_details"]
            try:
                all_states: List[
                    RIDAircraftState
                ] = my_telemetry_validator.parse_validate_current_states(
                    current_states=current_states
                )
                rid_flight_details = flight_details["rid_details"]
                f_details: RIDFlightDetails = (
                    my_telemetry_validator.parse_validate_rid_details(
                        rid_flight_details=rid_flight_details
                    )
                )

            except KeyError as ke:
                incorrect_parameters = {
                    "message": "A states object with a fully valid current states is necessary, the parsing the following key encountered errors %s"
                    % ke
                }
                return JsonResponse(
                    incorrect_parameters, status=400, content_type="application/json"
                )

            single_observation_set = SignedUnSignedTelemetryObservations(
                current_states=all_states, flight_details=f_details
            )

            unsigned_telemetry_observations.append(
                asdict(single_observation_set, dict_factory=NestedDict)
            )

            stream_rid_data_v22.delay(
                rid_telemetry_observations=json.dumps(unsigned_telemetry_observations)
            )
        submission_success = {"message": "Telemetry data successfully submitted"}
        content_digest = response_signer.generate_content_digest(submission_success)
        signed_data = response_signer.sign_json_via_django(submission_success)
        submission_success["signed"] = signed_data
        response = JsonResponse(
            submission_success, status=201, content_type="application/json"
        )
        response["Content-Digest"] = content_digest
        response["req"] = request.headers["Signature"]

        return response


def _parse_telemetry_request(json_payload):
    """
    Validate the JSON payload to make sure all required fields are provided and the flight times are in proper order
    """
    error = None
    telemetry_request = None
    serializer = TelemetryRequestSerializer(data=json_payload)
    if not serializer.is_valid():
        error = serializer.errors
        return telemetry_request, error

    validated_data = serializer.validated_data
    telemetry_request = serializer.create(validated_data)
    return telemetry_request, error


def _get_flight_details_from_observation(observation: TelemetryRequest):
    flight_details = observation["flight_details"]
    flight_details_json_str = json.dumps(flight_details)
    flight_details_json = json.loads(flight_details_json_str)

    parsed_flight_details = flight_detail_json_to_object(flight_details_json)
    return parsed_flight_details


def _get_current_states_from_observation(observation: TelemetryRequest):
    states = observation["current_states"]
    states_json_str = json.dumps(states, cls=DateTimeEncoder)
    states_json = json.loads(states_json_str)
    current_states: List[RIDAircraftState] = []
    for state_json in states_json:
        current_state = current_state_json_to_object(state_json)
        current_states.append(current_state)
    return current_states


@api_view(["PUT"])
@requires_scopes(["blender.write"])
def set_telemetry(request: HttpRequest):
    """
    A RIDOperatorDetails object is posted here
    This endpoints receives data from GCS and / or flights and processes remote ID data.
    """
    # TODO: Use dacite to parse incoming json into a dataclass
    stream = io.BytesIO(request.body)
    json_payload = JSONParser().parse(stream)

    parsed_telemetry_request, parse_error = _parse_telemetry_request(json_payload)
    if parse_error:
        return HttpResponse(
            json.dumps(parse_error),
            status=status.HTTP_400_BAD_REQUEST,
            content_type="application/json",
        )

    unsigned_telemetry_observations: List[SignedUnSignedTelemetryObservations] = []
    observations = parsed_telemetry_request.observations
    for observation in observations:
        flight_details = _get_flight_details_from_observation(observation)
        current_states: List[RIDAircraftState] = _get_current_states_from_observation(
            observation
        )

        single_observation_set = SignedUnSignedTelemetryObservations(
            current_states=current_states, flight_details=flight_details
        )

        unsigned_telemetry_observations.append(
            asdict(single_observation_set, dict_factory=NestedDict)
        )
        unsigned_telemetry_observations_str = json.dumps(
            unsigned_telemetry_observations
        )
        stream_rid_data_v22.delay(
            rid_telemetry_observations=unsigned_telemetry_observations_str
        )
    submission_success = {"message": "Telemetry data successfully submitted"}
    return JsonResponse(
        submission_success,
        status=status.HTTP_201_CREATED,
        content_type="application/json",
    )


@method_decorator(requires_scopes(["geo-awareness.test"]), name="dispatch")
class SignedTelmetryPublicKeyList(generics.ListCreateAPIView):
    queryset = SignedTelmetryPublicKey.objects.all()
    serializer_class = SignedTelmetryPublicKeySerializer


@method_decorator(requires_scopes(["geo-awareness.test"]), name="dispatch")
class SignedTelmetryPublicKeyDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = SignedTelmetryPublicKey.objects.all()
    serializer_class = SignedTelmetryPublicKeySerializer
