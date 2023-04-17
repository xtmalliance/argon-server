
from typing import List
from dacite import from_dict
from rid_operations.data_definitions import SubmittedTelemetryFlightDetails, SignedTelemetryRequest, RIDFlightDetails, RIDAircraftState, SignedUnSignedTelemetryObservations, Time, RIDOperationalStatus, RIDAircraftPosition, HorizontalAccuracy, VerticalAccuracy,RIDHeight, SpeedAccuracy, UAClassificationEU, UASID, OperatorLocation, LatLngPoint

def generate_rid_telemetry_objects(signed_telemetry_request: SignedTelemetryRequest) -> List[SubmittedTelemetryFlightDetails]:
    all_rid_data = []

    for current_signed_telemetry_request in signed_telemetry_request:

        s = from_dict(
                data_class = SubmittedTelemetryFlightDetails,
                data = current_signed_telemetry_request)        
        all_rid_data.append(s)

    return all_rid_data

def generate_unsigned_rid_telemetry_objects(telemetry_request: List[SignedUnSignedTelemetryObservations]) -> List[SubmittedTelemetryFlightDetails]:
    all_rid_data = []

    for current_unsigned_telemetry_request in telemetry_request:

        s = from_dict(
                data_class = SubmittedTelemetryFlightDetails,
                data = current_unsigned_telemetry_request)        
        all_rid_data.append(s)

    return all_rid_data


class BlenderTelemetryValidator():

    def parse_validate_current_parse_validate_current_statestates(self, current_states) ->List[RIDAircraftState]:
        all_states = []        

        for state in current_states:          

            timestamp = Time(value = state['timestamp']['value'], format = state['timestamp']['format'])
            operational_status = RIDOperationalStatus(state['operational_status'])
            _state_position = state['position']
            
            accuracy_h = HorizontalAccuracy(value =  _state_position['accuracy_h'])
            accuracy_v = VerticalAccuracy(value=_state_position['accuracy_v'])
            height = RIDHeight(reference= state['height']['reference'], distance = state['height']['distance'])

            position = RIDAircraftPosition(lat = _state_position['lat'], lng = _state_position['lng'], accuracy_h = accuracy_h, accuracy_v = accuracy_v, extrapolated = _state_position['extraplated'])
            speed_accuracy = SpeedAccuracy('SA3mps')


            s = RIDAircraftState(timestamp = timestamp, operational_status = operational_status, position = position, height=height, track = state['track'], speed = state['speed'], timestamp_accuracy = state['timestamp_accuracy'], speed_accuracy = speed_accuracy, vertical_speed = state['vertical_speed'])

            all_states.append(s)

        return all_states

    def parse_validate_rid_details(self, rid_flight_details)->RIDFlightDetails: 
        eu_classification = UAClassificationEU(rid_flight_details['eu_classification'])
        uas_id = UASID(serial_number=rid_flight_details['uas_id']['serial_number'] ,registration_id = rid_flight_details['uas_id']['registration_id'], utm_id = rid_flight_details['uas_id']['utm_id'] )
        operator_position = OperatorLocation(position = LatLngPoint(lat = rid_flight_details['operator_location']['lat'], lng =  rid_flight_details['operator_location']['lng']))
        operator_location = OperatorLocation(position = operator_position)

        f_details = RIDFlightDetails(id = rid_flight_details['id'], eu_classification = eu_classification, uas_id = uas_id, operator_location = operator_location, operator_id =rid_flight_details['operator_id'], operation_description =rid_flight_details['operator_description'] )
    
        return f_details

    def validate_flight_details_current_states_exist(self, flight) -> bool:
        try: 
            assert 'flight_details' in flight
            assert 'current_states' in flight
        except AssertionError as ae: 
            return False
        return True


        
    def validate_observations_exist(self, raw_request_data) -> bool:
        try:
            assert 'observations' in raw_request_data
        except AssertionError as ae: 
            return False
        return True


        