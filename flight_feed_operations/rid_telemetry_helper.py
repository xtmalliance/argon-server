from enum import Enum
from typing import List

from dacite import from_dict

from rid_operations.data_definitions import (
    UASID,
    HorizontalAccuracy,
    LatLngPoint,
    OperatorLocation,
    RIDAircraftPosition,
    RIDAircraftState,
    RIDAuthData,
    RIDFlightDetails,
    RIDHeight,
    RIDOperationalStatus,
    SignedTelemetryRequest,
    SignedUnSignedTelemetryObservations,
    SpeedAccuracy,
    SubmittedTelemetryFlightDetails,
    Time,
    UAClassificationEU,
    VerticalAccuracy,
)


class NestedDict(dict):
    def convert_value(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        return obj

    def __init__(self, data):
        super().__init__(self.convert_value(x) for x in data if x[1] is not None)


def generate_rid_telemetry_objects(
    signed_telemetry_request: SignedTelemetryRequest,
) -> List[SubmittedTelemetryFlightDetails]:
    all_rid_data = []

    for current_signed_telemetry_request in signed_telemetry_request:
        s = from_dict(
            data_class=SubmittedTelemetryFlightDetails,
            data=current_signed_telemetry_request,
        )
        all_rid_data.append(s)

    return all_rid_data


def generate_unsigned_rid_telemetry_objects(
    telemetry_request: List[SignedUnSignedTelemetryObservations],
) -> List[SubmittedTelemetryFlightDetails]:
    all_rid_data = []

    for current_unsigned_telemetry_request in telemetry_request:
        s = from_dict(
            data_class=SubmittedTelemetryFlightDetails,
            data=current_unsigned_telemetry_request,
        )
        all_rid_data.append(s)

    return all_rid_data


class BlenderTelemetryValidator:
    def parse_validate_current_state(self, current_state) -> RIDAircraftState:
        timestamp = Time(
            value=current_state["timestamp"]["value"],
            format=current_state["timestamp"]["format"],
        )
        operational_status = RIDOperationalStatus(current_state["operational_status"])
        _state_position = current_state["position"]
        # In provided telemetry position and pressure altitude and extrapolated values are optional use if provided else generate them.
        pressure_altitude = _state_position["pressure_altitude"] if "pressure_altitude" in _state_position else 0.0
        extrapolated = _state_position["extrapolated"] if "extrapolated" in _state_position else 0

        accuracy_h = HorizontalAccuracy(value=_state_position["accuracy_h"])
        accuracy_v = VerticalAccuracy(value=_state_position["accuracy_v"])
        height = RIDHeight(
            reference=current_state["height"]["reference"],
            distance=current_state["height"]["distance"],
        )

        position = RIDAircraftPosition(
            pressure_altitude=pressure_altitude,
            lat=_state_position["lat"],
            alt=_state_position["alt"],
            lng=_state_position["lng"],
            accuracy_h=accuracy_h,
            accuracy_v=accuracy_v,
            extrapolated=extrapolated,
            height=height,
        )
        speed_accuracy = SpeedAccuracy("SA3mps")

        s = RIDAircraftState(
            timestamp=timestamp,
            operational_status=operational_status,
            position=position,
            track=current_state["track"],
            speed=current_state["speed"],
            timestamp_accuracy=current_state["timestamp_accuracy"],
            speed_accuracy=speed_accuracy,
            vertical_speed=current_state["vertical_speed"],
        )

        return s

    def parse_validate_current_states(self, current_states) -> List[RIDAircraftState]:
        """This method parses and validates current state object and returns a dataclass"""

        all_states = []

        for state in current_states:
            s = self.parse_validate_current_state(current_state=state)
            all_states.append(s)
        return all_states

    def parse_validate_rid_details(self, rid_flight_details) -> RIDFlightDetails:
        if "eu_classification" in rid_flight_details.keys():
            eu_classification_details = rid_flight_details["eu_classification"]

            eu_classification = UAClassificationEU(
                category=eu_classification_details["category"],
                class_=eu_classification_details["class_"],
            )
        else:
            eu_classification = UAClassificationEU(category="", class_="")
        if "uas_id" in rid_flight_details.keys():
            uas_id_details = rid_flight_details["uas_id"]
            uas_id = UASID(
                serial_number=uas_id_details["serial_number"],
                registration_id=uas_id_details["registration_id"],
                utm_id=uas_id_details["utm_id"],
            )
        else:
            uas_id = UASID(serial_number="", registration_id="", utm_id="")
        if "operator_location" in rid_flight_details.keys():
            if "position" in rid_flight_details["operator_location"]:
                o_location_position = rid_flight_details["operator_location"]["position"]
                operator_position = LatLngPoint(lat=o_location_position["lat"], lng=o_location_position["lng"])
                operator_location = OperatorLocation(position=operator_position)
            else:
                operator_location = OperatorLocation(position=LatLngPoint(lat="", lng=""))
        else:
            operator_location = OperatorLocation(position=LatLngPoint(lat="", lng=""))

        auth_data = RIDAuthData(format="", data="")
        if "auth_data" in rid_flight_details.keys():
            if rid_flight_details["auth_data"] is not None:
                auth_data = RIDAuthData(
                    format=rid_flight_details["auth_data"]["format"],
                    data=rid_flight_details["auth_data"]["data"],
                )

        f_details = RIDFlightDetails(
            id=rid_flight_details["id"],
            eu_classification=eu_classification,
            uas_id=uas_id,
            operator_location=operator_location,
            operator_id=rid_flight_details["operator_id"],
            operation_description=rid_flight_details["operation_description"],
            auth_data=auth_data,
        )

        return f_details

    def validate_flight_details_current_states_exist(self, flight) -> bool:
        try:
            assert "flight_details" in flight
            assert "current_states" in flight
        except AssertionError:
            return False
        return True

    def validate_observation_key_exists(self, raw_request_data) -> bool:
        try:
            assert "observations" in raw_request_data
        except AssertionError:
            return False
        return True
