from rest_framework.decorators import api_view
from rest_framework import status
import json
import arrow
from typing import List
from auth_helper.utils import requires_scopes
from rest_framework.response import Response
from dataclasses import asdict, is_dataclass
from datetime import timedelta
from .scd_test_harness_helper import (
    conflict_with_flight_test_injection_response,
    planned_test_injection_response,
    ready_to_fly_injection_response,
    rejected_test_injection_response,
    failed_test_injection_response,
)
from .scd_data_definitions import (
    SCDTestInjectionDataPayload,
    FlightAuthorizationDataPayload,
    SCDTestStatusResponse,
    CapabilitiesResponse,
    DeleteFlightResponse,
    LatLngPoint,
    Polygon,
    Circle,
    Altitude,
    Volume3D,
    Time,
    Radius,
    Volume4D,
    OperationalIntentTestInjection,
    OperationalIntentStorage,
    ClearAreaResponse,
    ClearAreaResponseOutcome,
    SuccessfulOperationalIntentFlightIDStorage,
)
from . import dss_scd_helper
from rid_operations import rtree_helper
from .utils import UAVSerialNumberValidator, OperatorRegistrationNumberValidator
from django.http import JsonResponse
from auth_helper.common import get_redis
import logging
from uuid import UUID
from os import environ as env
from dotenv import load_dotenv, find_dotenv
from auth_helper.common import RedisHelper

load_dotenv(find_dotenv())
INDEX_NAME = "opint_proc"

logger = logging.getLogger("django")


def is_valid_uuid(uuid_to_test, version=4):
    try:
        uuid_obj = UUID(uuid_to_test, version=version)
    except ValueError:
        return False
    return str(uuid_obj) == uuid_to_test


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if is_dataclass(o):
            return asdict(o)
        return super().default(o)


@api_view(["GET"])
@requires_scopes(["utm.inject_test_data"])
def SCDTestStatus(request):
    status = SCDTestStatusResponse(status="Ready", version="latest")
    return JsonResponse(
        json.loads(json.dumps(status, cls=EnhancedJSONEncoder)), status=200
    )


@api_view(["GET"])
@requires_scopes(["utm.inject_test_data"])
def SCDTestCapabilities(request):
    status = CapabilitiesResponse(
        capabilities=[
            "BasicStrategicConflictDetection",
            "FlightAuthorisationValidation",
        ]
    )
    return JsonResponse(
        json.loads(json.dumps(status, cls=EnhancedJSONEncoder)), status=200
    )


@api_view(["POST"])
@requires_scopes(["utm.inject_test_data"])
def SCDClearAreaRequest(request):
    clear_area_request = request.data
    try:
        request_id = clear_area_request["request_id"]
        extent_raw = clear_area_request["extent"]
    except KeyError as ke:
        return Response(
            {
                "result": "Could not parse clear area payload, expected key %s not found "
                % ke
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    r = get_redis()
    # Convert the extent to V4D
    # my_redis_helper = RedisHelper()
    # my_redis_helper.delete_all_opints()

    # Create a list of Volume4D objects
    my_operational_intent_parser = dss_scd_helper.OperationalIntentReferenceHelper()
    volume4D = my_operational_intent_parser.parse_volume_to_volume4D(volume=extent_raw)
    my_geo_json_converter = dss_scd_helper.VolumesConverter()

    my_geo_json_converter.convert_volumes_to_geojson(volumes=[volume4D])
    view_rect_bounds = my_geo_json_converter.get_bounds()
    my_rtree_helper = rtree_helper.OperationalIntentsIndexFactory(index_name=INDEX_NAME)
    my_rtree_helper.generate_operational_intents_index(pattern="flight_opint.*")
    op_ints_exist = my_rtree_helper.check_op_ints_exist()
    all_existing_op_ints_in_area = []
    if op_ints_exist:
        all_existing_op_ints_in_area = my_rtree_helper.check_box_intersection(
            view_box=view_rect_bounds
        )

    all_deletion_requests_status = []
    if all_existing_op_ints_in_area:
        for flight_details in all_existing_op_ints_in_area:
            if flight_details:
                deletion_success = False
                operation_id = flight_details["flight_id"]
                op_int_details_key = "flight_opint." + operation_id
                if r.exists(op_int_details_key):
                    op_int_detail_raw = r.get(op_int_details_key)
                    my_scd_dss_helper = dss_scd_helper.SCDOperations()
                    # op_int_detail_raw = op_int_details.decode()
                    op_int_detail = json.loads(op_int_detail_raw)
                    ovn = op_int_detail["success_response"][
                        "operational_intent_reference"
                    ]["ovn"]
                    opint_id = op_int_detail["success_response"][
                        "operational_intent_reference"
                    ]["id"]
                    ovn_opint = {"ovn_id": ovn, "opint_id": opint_id}
                    logger.info(
                        "Deleting operational intent {opint_id} with ovn {ovn_id}".format(
                            **ovn_opint
                        )
                    )

                    deletion_request = my_scd_dss_helper.delete_operational_intent(
                        dss_operational_intent_ref_id=opint_id, ovn=ovn
                    )

                    if deletion_request.status == 200:
                        logger.info(
                            "Success in deleting operational intent {opint_id} with ovn {ovn_id}".format(
                                **ovn_opint
                            )
                        )
                        deletion_success = True
                    all_deletion_requests_status.append(deletion_success)
        clear_area_status = ClearAreaResponseOutcome(
            success=all(all_deletion_requests_status),
            message="All operational intents in the area cleared successfully",
            timestamp=arrow.now().isoformat(),
        )

    else:
        clear_area_status = ClearAreaResponseOutcome(
            success=True,
            message="All operational intents in the area cleared successfully",
            timestamp=arrow.now().isoformat(),
        )
    my_rtree_helper.clear_rtree_index(pattern="flight_opint.*")
    clear_area_response = ClearAreaResponse(outcome=clear_area_status)
    return JsonResponse(
        json.loads(json.dumps(clear_area_response, cls=EnhancedJSONEncoder)), status=200
    )


@api_view(["PUT", "DELETE"])
@requires_scopes(["utm.inject_test_data"])
def SCDAuthTest(request, operation_id):
    # This view implementes the automated verification of SCD capabilities
    r = get_redis()
    if request.method == "PUT":
        my_operational_intent_parser = dss_scd_helper.OperationalIntentReferenceHelper()
        my_scd_dss_helper = dss_scd_helper.SCDOperations()
        my_geo_json_converter = dss_scd_helper.VolumesConverter()
        my_volumes_validator = dss_scd_helper.VolumesValidator()

        # Get the test data
        scd_test_data = request.data
        # Prase the flight authorization data set
        try:
            flight_authorization_data = scd_test_data["flight_authorisation"]
            f_a = FlightAuthorizationDataPayload(
                uas_serial_number=flight_authorization_data["uas_serial_number"],
                operation_category=flight_authorization_data["operation_category"],
                operation_mode=flight_authorization_data["operation_mode"],
                uas_class=flight_authorization_data["uas_class"],
                identification_technologies=flight_authorization_data[
                    "identification_technologies"
                ],
                connectivity_methods=flight_authorization_data["connectivity_methods"],
                endurance_minutes=flight_authorization_data["endurance_minutes"],
                emergency_procedure_url=flight_authorization_data[
                    "emergency_procedure_url"
                ],
                operator_id=flight_authorization_data["operator_id"],
            )
        except KeyError as ke:
            return Response(
                {
                    "result": "Could not parse test injection payload, expected key %s not found "
                    % ke
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Set up initial data
        now = arrow.now()

        # # Create a index and see what is already in Blender
        # my_rtree_helper = rtree_helper.OperationalIntentsIndexFactory(
        #     index_name=INDEX_NAME
        # )
        # # Create a index of existing opints
        # my_rtree_helper.generate_operational_intents_index(pattern="flight_opint.*")

        # Initial data for subscriptions
        one_minute_from_now = now.shift(minutes=1)
        one_minute_from_now_str = one_minute_from_now.isoformat()
        two_minutes_from_now = now.shift(minutes=2)
        two_minutes_from_now_str = two_minutes_from_now.isoformat()
        opint_subscription_end_time = timedelta(seconds=180)
        # TODO use ImplicitDict for this
        # Parse the operational intent
        try:
            operational_intent = scd_test_data["operational_intent"]
            operational_intent_volumes = operational_intent["volumes"]
            operational_intent_off_nominal_volumes = operational_intent[
                "off_nominal_volumes"
            ]
        except KeyError as ke:
            return Response(
                {
                    "result": "Could not parse test injection payload, expected key %s not found "
                    % ke
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create a list of Volume4D objects
        all_volumes: List[Volume4D] = []
        for volume in operational_intent_volumes:
            v4D = my_operational_intent_parser.parse_volume_to_volume4D(volume=volume)
            all_volumes.append(v4D)

        # Create a list of Volume4D objects
        all_off_nominal_volumes: List[Volume4D] = []
        for off_nominal_volume in operational_intent_off_nominal_volumes:
            v4D = my_operational_intent_parser.parse_volume_to_volume4D(
                volume=off_nominal_volume
            )
            all_off_nominal_volumes.append(v4D)

        # Get THe state of the test data is coming in
        test_state = operational_intent["state"]
        # Parse the intent data and
        operational_intent_data = OperationalIntentTestInjection(
            volumes=all_volumes,
            priority=operational_intent["priority"],
            off_nominal_volumes=all_off_nominal_volumes,
            state=test_state,
        )
        # End parse the operational intent
        # Begin validation of operational intent
        my_operational_intent_validator = dss_scd_helper.OperationalIntentValidator(
            operational_intent_data=operational_intent_data
        )
        operational_intent_valid = (
            my_operational_intent_validator.validate_operational_intent_test_data()
        )

        if not operational_intent_valid:
            return Response(
                json.loads(
                    json.dumps(
                        rejected_test_injection_response, cls=EnhancedJSONEncoder
                    )
                ),
                status=status.HTTP_200_OK,
            )
        # End validation of operational intent
        # Set the object for SCD Test Injection
        test_injection_data = SCDTestInjectionDataPayload(
            operational_intent=operational_intent_data, flight_authorisation=f_a
        )
        volumes_valid = my_volumes_validator.validate_volumes(
            volumes=test_injection_data.operational_intent.volumes
        )

        if not volumes_valid:
            return Response(
                json.loads(
                    json.dumps(
                        rejected_test_injection_response, cls=EnhancedJSONEncoder
                    )
                ),
                status=status.HTTP_200_OK,
            )

        # Check flight auth data first before going to DSS
        my_serial_number_validator = UAVSerialNumberValidator(
            serial_number=test_injection_data.flight_authorisation.uas_serial_number
        )
        my_reg_number_validator = OperatorRegistrationNumberValidator(
            operator_registration_number=test_injection_data.flight_authorisation.operator_id
        )

        is_serial_number_valid = my_serial_number_validator.is_valid()
        is_reg_number_valid = my_reg_number_validator.is_valid()

        if not is_serial_number_valid:
            injection_response = asdict(rejected_test_injection_response)
            return Response(
                json.loads(json.dumps(injection_response, cls=EnhancedJSONEncoder)),
                status=status.HTTP_200_OK,
            )

        if not is_reg_number_valid:
            injection_response = asdict(rejected_test_injection_response)
            return Response(
                json.loads(json.dumps(injection_response, cls=EnhancedJSONEncoder)),
                status=status.HTTP_200_OK,
            )

        my_geo_json_converter.convert_volumes_to_geojson(volumes=all_volumes)
        view_rect_bounds = my_geo_json_converter.get_bounds()

        auth_token = my_scd_dss_helper.get_auth_token()
        try:
            assert "error" not in auth_token
        except AssertionError as e:
            logging.error(
                "Error in retrieving auth_token, check if the auth server is running properly, error details below"
            )
            logging.error(auth_token["error"])
            failed_test_injection_response.notes
            return Response(
                json.loads(
                    json.dumps(failed_test_injection_response, cls=EnhancedJSONEncoder)
                ),
                status=status.HTTP_200_OK,
            )
        print('+++++++++++++++++++++++++++++++++')
        print(scd_test_data['operational_intent']['state'])
        print('+++++++++++++++++++++++++++++++++')
        # Operational intents valid and now send to DSS
        op_int_submission = my_scd_dss_helper.create_and_submit_operational_intent_reference(
            state=test_injection_data.operational_intent.state,
            volumes=test_injection_data.operational_intent.volumes,
            off_nominal_volumes=test_injection_data.operational_intent.off_nominal_volumes,
            priority=test_injection_data.operational_intent.priority,
        )

        if op_int_submission.status == "success":
            # Successfully submitted to the DSS, save the operational intent in Redis
            view_r_bounds = ",".join(map(str, view_rect_bounds))
            operational_intent_full_details = OperationalIntentStorage(
                bounds=view_r_bounds,
                start_time=one_minute_from_now_str,
                end_time=two_minutes_from_now_str,
                alt_max=50,
                alt_min=25,
                success_response=op_int_submission.dss_response,
                operational_intent_details=test_injection_data.operational_intent,
            )
            # Store flight DSS response and operational intent reference
            flight_opint = "flight_opint." + str(operation_id)
            logging.info(
                "Flight with operational intent id {flight_opint} created".format(
                    flight_opint=str(operation_id)
                )
            )
            r.set(flight_opint, json.dumps(asdict(operational_intent_full_details)))
            r.expire(name=flight_opint, time=opint_subscription_end_time)

            # Store the details of the operational intent reference
            flight_op_int_storage = SuccessfulOperationalIntentFlightIDStorage(
                operation_id=str(operation_id),
                operational_intent_id=op_int_submission.operational_intent_id,
            )
            opint_flightref = (
                "opint_flightref." + op_int_submission.operational_intent_id
            )

            r.set(opint_flightref, json.dumps(asdict(flight_op_int_storage)))
            r.expire(name=opint_flightref, time=opint_subscription_end_time)
            # End store flight DSS

            planned_test_injection_response.operational_intent_id = (
                op_int_submission.operational_intent_id
            )

        elif op_int_submission.status == "conflict_with_flight":
            # If conflict with flight is generated then no need to save response
            conflict_with_flight_test_injection_response.operational_intent_id = (
                op_int_submission.operational_intent_id
            )
            return Response(
                json.loads(
                    json.dumps(
                        conflict_with_flight_test_injection_response,
                        cls=EnhancedJSONEncoder,
                    )
                ),
                status=status.HTTP_200_OK,
            )
        else:
            # If conflict with flight is generated then no need to save response
            failed_test_injection_response.operational_intent_id = (
                op_int_submission.operational_intent_id
            )
            return Response(
                json.loads(
                    json.dumps(failed_test_injection_response, cls=EnhancedJSONEncoder)
                ),
                status=status.HTTP_200_OK,
            )

        if test_injection_data.operational_intent.state == "Activated":
            return Response(
                json.loads(
                    json.dumps(ready_to_fly_injection_response, cls=EnhancedJSONEncoder)
                ),
                status=status.HTTP_200_OK,
            )
        else:
            try:
                injection_response = asdict(planned_test_injection_response)

                return Response(
                    json.loads(json.dumps(injection_response, cls=EnhancedJSONEncoder)),
                    status=status.HTTP_200_OK,
                )
            except KeyError as ke:
                injection_response = asdict(failed_test_injection_response)
                return Response(
                    json.loads(json.dumps(injection_response, cls=EnhancedJSONEncoder)),
                    status=status.HTTP_400_BAD_REQUEST,
                )

    elif request.method == "DELETE":
        op_int_details_key = "flight_opint." + str(operation_id)
        op_int_detail_raw = r.get(op_int_details_key)

        if op_int_detail_raw:
            my_scd_dss_helper = dss_scd_helper.SCDOperations()
            op_int_detail = json.loads(op_int_detail_raw)

            ovn = op_int_detail["success_response"]["operational_intent_reference"][
                "ovn"
            ]
            opint_id = op_int_detail["success_response"][
                "operational_intent_reference"
            ]["id"]
            ovn_opint = {"ovn_id": ovn, "opint_id": opint_id}
            logger.info(
                "Deleting operational intent {opint_id} with ovn {ovn_id}".format(
                    **ovn_opint
                )
            )
            my_scd_dss_helper.delete_operational_intent(
                dss_operational_intent_ref_id=opint_id, ovn=ovn
            )
            # r.delete(op_int_details_key)

            delete_flight_response = DeleteFlightResponse(
                result="Closed",
                notes="The flight was closed successfully by the USS and is now out of the UTM system.",
            )
        else:
            delete_flight_response = DeleteFlightResponse(
                result="Failed",
                notes="The flight was not found in the USS, please check your flight ID %s"
                % operation_id,
            )

        return Response(
            json.loads(json.dumps(delete_flight_response, cls=EnhancedJSONEncoder)),
            status=status.HTTP_200_OK,
        )
