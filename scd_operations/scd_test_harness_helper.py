import json
from typing import List

from auth_helper.common import get_redis
from rid_operations import rtree_helper

from .dss_scd_helper import OperationalIntentReferenceHelper, VolumesConverter
from .scd_data_definitions import TestInjectionResult, Volume4D

# Set the responses to be used
failed_test_injection_response = TestInjectionResult(
    result="Failed",
    notes="Processing of operational intent has failed",
    operational_intent_id="",
)
rejected_test_injection_response = TestInjectionResult(
    result="Rejected",
    notes="An existing operational intent already exists and conflicts in space and time",
    operational_intent_id="",
)
planned_test_injection_response = TestInjectionResult(
    result="Planned",
    notes="Successfully created operational intent in the DSS",
    operational_intent_id="",
)
conflict_with_flight_test_injection_response = TestInjectionResult(
    result="ConflictWithFlight",
    notes="Processing of operational intent has failed, flight not deconflicted",
    operational_intent_id="",
)
ready_to_fly_injection_response = TestInjectionResult(
    result="ReadyToFly",
    notes="Processing of operational intent succeeded, flight is activated",
    operational_intent_id="",
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

            reference_full = op_int_details["success_response"]["operational_intent_reference"]
            details_full = op_int_details["operational_intent_details"]
            # Load existing opint details
            operational_intent_reference = self.my_operational_intent_helper.parse_operational_intent_reference_from_dss(
                operational_intent_reference=reference_full
            )
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
