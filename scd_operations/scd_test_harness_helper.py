import json
from enum import Enum
from typing import List

import dacite
from dacite import from_dict

from auth_helper.common import get_redis
from rid_operations import rtree_helper

from .dss_scd_helper import OperationalIntentReferenceHelper, VolumesConverter
from .flight_planning_data_definitions import (
    ASTMF354821OpIntentInformation,
    BasicFlightPlanInformation,
    FlightAuthorisationData,
    FlightPlan,
    FlightPlanAdvisoriesEnum,
    FlightPlanningRequest,
    FlightPlanProcessingResultEnum,
    RPAS26FlightDetails,
    UpsertFlightPlanResponse,
)
from .scd_data_definitions import (
    TestInjectionResult,
    TestInjectionResultState,
    Volume4D,
)

# Set the responses to be used
failed_test_injection_response = TestInjectionResult(
    result=TestInjectionResultState.Failed,
    notes="Processing of operational intent has failed",
    operational_intent_id="",
)
rejected_test_injection_response = TestInjectionResult(
    result=TestInjectionResultState.Rejected,
    notes="An existing operational intent already exists and conflicts in space and time",
    operational_intent_id="",
)
planned_test_injection_response = TestInjectionResult(
    result=TestInjectionResultState.Planned,
    notes="Successfully created operational intent in the DSS",
    operational_intent_id="",
)
conflict_with_flight_test_injection_response = TestInjectionResult(
    result=TestInjectionResultState.ConflictWithFlight,
    notes="Processing of operational intent has failed, flight not deconflicted",
    operational_intent_id="",
)
ready_to_fly_injection_response = TestInjectionResult(
    result=TestInjectionResultState.ReadyToFly,
    notes="Processing of operational intent succeeded, flight is activated",
    operational_intent_id="",
)

# Flight Planning responses
not_supported_planning_response = UpsertFlightPlanResponse(
    result=FlightPlanProcessingResultEnum.NotSupported,
    notes="Flight Plan action is not supported",
    includes_advisories=FlightPlanAdvisoriesEnum.No,
)
planned_planning_response = UpsertFlightPlanResponse(
    result=FlightPlanProcessingResultEnum.Planned,
    notes="Flight Plan successfully processed and flight planned",
    includes_advisories=FlightPlanAdvisoriesEnum.No,
)

ready_to_fly_planning_response = UpsertFlightPlanResponse(
    result=FlightPlanProcessingResultEnum.ReadyToFly,
    notes="Flight is ready to fly",
    includes_advisories=FlightPlanAdvisoriesEnum.No,
)

rejected_planning_response = UpsertFlightPlanResponse(
    result=FlightPlanProcessingResultEnum.Rejected,
    notes="Flight Planning rejected this flight",
    includes_advisories=FlightPlanAdvisoriesEnum.No,
)

failed_planning_response = UpsertFlightPlanResponse(
    result=FlightPlanProcessingResultEnum.Failed,
    notes="Flight Planning failed to process this flight",
    includes_advisories=FlightPlanAdvisoriesEnum.No,
)


class SCDTestHarnessHelper:
    """This class is used in the SCD Test harness to include transformations"""

    def __init__(self):
        self.my_operational_intent_helper = OperationalIntentReferenceHelper()
        self.r = get_redis()
        self.my_volumes_converter = VolumesConverter()
        self.my_operational_intent_comparator = rtree_helper.OperationalIntentComparisonFactory()

    def check_if_same_flight_id_exists(self, operation_id: str) -> bool:
        r = get_redis()
        flight_opint = "flight_opint." + operation_id
        if r.exists(flight_opint):
            return True
        else:
            return False

    def check_if_same_operational_intent_exists_in_blender(self, volumes: List[Volume4D]) -> bool:
        all_checks: List[bool] = []
        self.my_volumes_converter.convert_volumes_to_geojson(volumes=volumes)
        polygon_to_check = self.my_volumes_converter.get_minimum_rotated_rectangle()

        # Get the volume to check
        all_opints = self.r.keys(pattern="flight_opint.*")
        for flight_opint in all_opints:
            stored_opint_volumes_converter = VolumesConverter()
            op_int_details_raw = self.r.get(flight_opint)
            op_int_details = json.loads(op_int_details_raw)

            details_full = op_int_details["operational_intent_details"]
            # Load existing opint details
            # reference_full = op_int_details["success_response"]["operational_intent_reference"]
            # operational_intent_reference = self.my_operational_intent_helper.parse_operational_intent_reference_from_dss(
            #     operational_intent_reference=reference_full
            # )
            stored_priority = details_full["priority"]
            stored_off_nominal_volumes = details_full["off_nominal_volumes"]
            operational_intent_details = self.my_operational_intent_helper.parse_operational_intent_details(
                operational_intent_details=details_full,
                priority=stored_priority,
                off_nominal_volumes=stored_off_nominal_volumes,
            )
            stored_volumes = operational_intent_details.volumes
            stored_opint_volumes_converter.convert_volumes_to_geojson(volumes=stored_volumes)
            stored_volume_polygon = stored_opint_volumes_converter.get_minimum_rotated_rectangle()
            are_polygons_same = self.my_operational_intent_comparator.check_volume_geometry_same(
                polygon_a=polygon_to_check, polygon_b=stored_volume_polygon
            )
            # Check if start and end times are equal
            # Check if altitude is equal
            all_checks.append(are_polygons_same)

        return all(all_checks)


class FlightPlanningDataProcessor:
    def __init__(self, incoming_flight_information: dict):
        self.incoming_flight_information = incoming_flight_information

        if not self.incoming_flight_information.keys() & {"intended_flight", "request_id"}:
            raise ValueError("Some requested_flight and request_id must be present in the incoming data")

        self.intended_flight_information = self.incoming_flight_information["intended_flight"]
        self.request_id = self.incoming_flight_information["request_id"]

        if not self.intended_flight_information.keys() & {
            "basic_information",
            "astm_f3548_21",
            "uspace_flight_authorisation",
            "rpas_operating_rules_2_6",
            "additional_information",
        }:
            raise ValueError("Some keys are missing")

    def process_basic_flight_plan(self, basic_information_dict) -> BasicFlightPlanInformation:
        basic_flight_plan_information = from_dict(
            data_class=BasicFlightPlanInformation, data=basic_information_dict, config=dacite.Config(cast=[Enum])
        )

        return basic_flight_plan_information

    def process_f3548_21_flight_plan_information(self, astm_f3548_op_int_information_dict) -> ASTMF354821OpIntentInformation:
        basic_flight_plan_information = from_dict(
            data_class=ASTMF354821OpIntentInformation, data=astm_f3548_op_int_information_dict, config=dacite.Config(cast=[Enum])
        )

        return basic_flight_plan_information

    def process_uspace_flight_authorisation_information(self, uspace_flight_authorisation_information_dict) -> FlightAuthorisationData:
        uspace_flight_authorisation = from_dict(
            data_class=FlightAuthorisationData, data=uspace_flight_authorisation_information_dict, config=dacite.Config(cast=[Enum])
        )

        return uspace_flight_authorisation

    def process_rpas_operating_rules_2_6_information(self, rpas_operating_rules_2_6_information_dict) -> RPAS26FlightDetails:
        rpas_operating_rules_2_6 = from_dict(
            data_class=RPAS26FlightDetails, data=rpas_operating_rules_2_6_information_dict, config=dacite.Config(cast=[Enum])
        )

        return rpas_operating_rules_2_6

    def process_additional_information(self) -> dict:
        additional_information = {}
        return additional_information

    def process_intended_flight_data(self) -> FlightPlan:
        basic_information = self.process_basic_flight_plan(basic_information_dict=self.intended_flight_information["basic_information"])
        astm_f3548_21 = self.process_f3548_21_flight_plan_information(
            astm_f3548_op_int_information_dict=self.intended_flight_information["astm_f3548_21"]
        )
        uspace_flight_authorisation = self.process_uspace_flight_authorisation_information(
            self.intended_flight_information["uspace_flight_authorisation"]
        )
        rpas_operating_rules_2_6 = self.process_rpas_operating_rules_2_6_information(self.intended_flight_information["rpas_operating_rules_2_6"])
        additional_information = self.process_additional_information()
        flight_plan = FlightPlan(
            basic_information=basic_information,
            astm_f3548_21=astm_f3548_21,
            uspace_flight_authorisation=uspace_flight_authorisation,
            rpas_operating_rules_2_6=rpas_operating_rules_2_6,
            additional_information=additional_information,
        )

        return flight_plan

    def process_incoming_flight_plan_data(self) -> FlightPlanningRequest:
        intended_flight = self.process_intended_flight_data()
        flight_planning_request = FlightPlanningRequest(intended_flight=intended_flight, request_id=self.request_id)
        return flight_planning_request
