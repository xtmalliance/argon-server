from rest_framework.decorators import api_view
from rest_framework import status
import json
from rest_framework.response import Response
from dataclasses import asdict
from rest_framework.views import APIView
from .data_definitions import FlightAuthorizationOperatorDataPayload, OperatorDataPayload, TestInjectionResult
from .utils import UAVSerialNumberValidator, OperatorRegistrationNumberValidator
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

@api_view(['PUT'])
def operator_auth_test(request):
    return Response({"message":"OK"}, status = status.HTTP_200_OK)


class SCDAuthTest(APIView):
    authentication_classes = [] #disables authentication
    permission_classes = [] #disables permission
    
    def put(self, request, flight_id):

        failed_test_injection_response = TestInjectionResult(result = "Failed", notes="",operational_intent_id ="")        
        rejected_test_injection_response = TestInjectionResult(result = "Rejected", notes="",operational_intent_id ="")
        planned_test_injection_response = TestInjectionResult(result = "Planned", notes="",operational_intent_id ="")

        scd_test_data = request.data        
        try:
            flight_authorization_data = scd_test_data['flight_authorisation']
            o_d = FlightAuthorizationOperatorDataPayload(uas_serial_number = flight_authorization_data['uas_serial_number'],operation_category = flight_authorization_data['operation_category'], operation_mode = flight_authorization_data['operation_mode'], uas_class = flight_authorization_data['uas_class'], identification_technologies = flight_authorization_data['identification_technologies'],connectivity_methods = flight_authorization_data['connectivity_methods'],  endurance_minutes = flight_authorization_data['endurance_minutes'], emergency_procedure_url = flight_authorization_data['emergency_procedure_url'],operator_id = flight_authorization_data['operator_id'])

            operator_data_payload = OperatorDataPayload(priority=1, flight_authorisation= o_d)

        except KeyError as ke:
            return Response({"result":"Could not parse payload, expected key %s not found " % ke }, status = status.HTTP_400_BAD_REQUEST)
        
        
        my_serial_number_validator = UAVSerialNumberValidator(serial_number = o_d.uas_serial_number)
        my_reg_number_validator = OperatorRegistrationNumberValidator(operator_registration_number = o_d.operator_id)

        is_serial_number_valid = my_serial_number_validator.is_valid()
        is_reg_number_valid = my_reg_number_validator.is_valid()
            
        if not is_serial_number_valid:
            injection_response = asdict(rejected_test_injection_response)
            return Response(json.loads(json.dumps(injection_response)), status = status.HTTP_403_FORBIDDEN)
        
        if not is_reg_number_valid:            
            injection_response = asdict(rejected_test_injection_response)
            return Response(json.loads(json.dumps(injection_response)), status = status.HTTP_403_FORBIDDEN)
              
        try: 
            injection_response = asdict(planned_test_injection_response)            
            return Response(json.loads(json.dumps(injection_response)), status = status.HTTP_200_OK)

        except KeyError as ke:
            injection_response = asdict(failed_test_injection_response)            
            return Response(json.loads(json.dumps(injection_response)), status = status.HTTP_400_BAD_REQUEST)
        