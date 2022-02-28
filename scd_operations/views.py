from rest_framework.decorators import api_view
from rest_framework import status
import json
from auth_helper.utils import requires_scopes
from rest_framework.response import Response
from dataclasses import asdict
from .scd_data_definitions import SCDTestInjectionDataPayload, FlightAuthorizationDataPayload, TestInjectionResult,StatusResponse, DeleteFlightResponse,LatLngPoint, Polygon, Circle, Altitude, Volume3D, Time, Radius, Volume4D, OperationalIntentTestInjection
from .utils import UAVSerialNumberValidator, OperatorRegistrationNumberValidator
from django.http import JsonResponse
import dataclasses
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())


class EnhancedJSONEncoder(json.JSONEncoder):
        def default(self, o):
            if dataclasses.is_dataclass(o):
                return dataclasses.asdict(o)
            return super().default(o)

@api_view(['GET'])
@requires_scopes(['utm.inject_test_data'])
def SCDTestStatus(request):
    status = StatusResponse(status="Ready")
    return JsonResponse(json.loads(json.dumps(status, cls=EnhancedJSONEncoder)), status=200)

@api_view(['PUT','DELETE'])
@requires_scopes(['utm.inject_test_data'])
def SCDAuthTest(request, flight_id):
    if request.method == "PUT":
        failed_test_injection_response = TestInjectionResult(result = "Failed", notes="",operational_intent_id ="")        
        rejected_test_injection_response = TestInjectionResult(result = "Rejected", notes="",operational_intent_id ="")
        planned_test_injection_response = TestInjectionResult(result = "Planned", notes="",operational_intent_id ="")

        scd_test_data = request.data        
        try:
            flight_authorization_data = scd_test_data['flight_authorisation']
            f_a = FlightAuthorizationDataPayload(uas_serial_number = flight_authorization_data['uas_serial_number'],operation_category = flight_authorization_data['operation_category'], operation_mode = flight_authorization_data['operation_mode'], uas_class = flight_authorization_data['uas_class'], identification_technologies = flight_authorization_data['identification_technologies'],connectivity_methods = flight_authorization_data['connectivity_methods'],  endurance_minutes = flight_authorization_data['endurance_minutes'], emergency_procedure_url = flight_authorization_data['emergency_procedure_url'],operator_id = flight_authorization_data['operator_id'])

            operational_intent = scd_test_data['operational_intent']
            operational_intent_volumes = operational_intent['volumes']
            all_volumes = []
            for volume in operational_intent_volumes:
                outline_polygon = None
                outline_circle = None

                if 'outline_polygon' in volume['volume'].keys():
                    all_vertices = volume['volume']['outline_polygon']['vertices']
                    polygon_verticies = []
                    for vertex in all_vertices:
                        v = LatLngPoint(lat = vertex['lat'],lng=vertex['lng'])
                        polygon_verticies.append(v)

                    outline_polygon = Polygon(vertices=polygon_verticies)

                if 'outline_circle' in volume['volume'].keys():                
                    circle_center =  LatLngPoint(lat = volume['volume']['outline_circle']['center']['lat'], lng = volume['volume']['outline_circle']['center']['lng'])
                    circle_radius = Radius(value =volume['volume']['outline_circle']['radius']['value'], units = volume['volume']['outline_circle']['radius']['units'])
                                    
                    outline_circle = Circle(center =circle_center, radius=circle_radius)
                    
                altitude_lower = Altitude(value = volume['volume']['altitude_lower']['value'],reference= volume['volume']['altitude_lower']['reference'], units =volume['volume']['altitude_lower']['units'] )
                altitude_upper = Altitude(value = volume['volume']['altitude_upper']['value'],reference=  volume['volume']['altitude_upper']['reference'], units =volume['volume']['altitude_upper']['units'] )                        
                volume3D = Volume3D(outline_circle=outline_circle, outline_polygon=outline_polygon, altitude_lower = altitude_lower, altitude_upper= altitude_upper)
                time_start = Time(format = volume['time_start']['format'], value = volume['time_start']['value'])
                time_end = Time(format =volume['time_end']['format'] , value = volume['time_end']['value'])
                volume4D = Volume4D(volume=volume3D, time_start=time_start, time_end=time_end)
                all_volumes.append(volume4D)
                
            operational_intent_data = OperationalIntentTestInjection(volumes = all_volumes, priority =1, off_nomial_volumes = operational_intent['off_nomial_volumes'], state= operational_intent['state'])

            operator_data_payload = FlightAuthorizationDataPayload(operational_intent=operational_intent_data, flight_authorisation= f_a)

        except KeyError as ke:
            return Response({"result":"Could not parse test injection payload, expected key %s not found " % ke }, status = status.HTTP_400_BAD_REQUEST)
        
        
        my_serial_number_validator = UAVSerialNumberValidator(serial_number = flight_authorization_data.uas_serial_number)
        my_reg_number_validator = OperatorRegistrationNumberValidator(operator_registration_number = flight_authorization_data.operator_id)

        is_serial_number_valid = my_serial_number_validator.is_valid()
        is_reg_number_valid = my_reg_number_validator.is_valid()
            
        if not is_serial_number_valid:
            injection_response = asdict(rejected_test_injection_response)
            return Response(json.loads(json.dumps(injection_response, cls=EnhancedJSONEncoder)), status = status.HTTP_403_FORBIDDEN)
        
        if not is_reg_number_valid:            
            injection_response = asdict(rejected_test_injection_response)
            return Response(json.loads(json.dumps(injection_response, cls=EnhancedJSONEncoder)), status = status.HTTP_403_FORBIDDEN)
                
        try: 
            injection_response = asdict(planned_test_injection_response)            
            return Response(json.loads(json.dumps(injection_response, cls=EnhancedJSONEncoder)), status = status.HTTP_200_OK)

        except KeyError as ke:
            injection_response = asdict(failed_test_injection_response)            
            return Response(json.loads(json.dumps(injection_response, cls=EnhancedJSONEncoder)), status = status.HTTP_400_BAD_REQUEST)

    elif request.method == "DELETE":
        delete_flight_response = DeleteFlightResponse(result="Closed", notes="The flight was closed successfully by the USS and is now out of the UTM system. ")

        return Response(json.loads(json.dumps(delete_flight_response, cls=EnhancedJSONEncoder)), status = status.HTTP_200_OK)