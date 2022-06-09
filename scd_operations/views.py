from rest_framework.decorators import api_view
from rest_framework import status
import json
import arrow
from auth_helper.utils import requires_scopes
from rest_framework.response import Response
from dataclasses import asdict, is_dataclass
from datetime import timedelta
from .scd_data_definitions import SCDTestInjectionDataPayload, FlightAuthorizationDataPayload, TestInjectionResult,StatusResponse, CapabilitiesResponse, DeleteFlightResponse,LatLngPoint, Polygon, Circle, Altitude, Volume3D, Time, Radius, Volume4D, OperationalIntentTestInjection, OperationalIntentStorage, ClearAreaResponse, SuccessfulOperationalIntentFlightIDStorage
from . import dss_scd_helper
from rid_operations import rtree_helper
from .utils import UAVSerialNumberValidator, OperatorRegistrationNumberValidator
from django.http import JsonResponse
import uuid
import redis
from auth_helper.common import get_redis
import logging
from uuid import UUID
from os import environ as env
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
INDEX_NAME = 'opint_proc'

logger = logging.getLogger('django')

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

@api_view(['GET'])
@requires_scopes(['utm.inject_test_data'])
def SCDTestStatus(request):
    status = StatusResponse(status="Ready", version="latest")
    return JsonResponse(json.loads(json.dumps(status, cls=EnhancedJSONEncoder)), status=200)

@api_view(['GET'])
@requires_scopes(['utm.inject_test_data'])
def SCDTestCapabilities(request):
    status = CapabilitiesResponse(capabilities =["BasicStrategicConflictDetection", "FlightAuthorisationValidation"])
    return JsonResponse(json.loads(json.dumps(status, cls=EnhancedJSONEncoder)), status=200)

@api_view(['POST'])
@requires_scopes(['utm.inject_test_data'])
def SCDClearAreaRequest(request):
    clear_area_request = request.data
    try:
        request_id = clear_area_request['request_id']
        extent = clear_area_request['extent']
    except KeyError as ke: 
        return Response({"result":"Could not parse clear area payload, expected key %s not found " % ke }, status = status.HTTP_400_BAD_REQUEST)
    
    r = get_redis()
    my_geo_json_converter = dss_scd_helper.VolumesConverter()
    my_geo_json_converter.convert_volumes_to_geojson(volumes = extent)
    view_rect_bounds = my_geo_json_converter.get_bounds()

    my_rtree_helper = rtree_helper.OperationalIntentsIndexFactory(index_name=INDEX_NAME)
    my_rtree_helper.generate_operational_intents_index()

    all_existing_op_ints_in_area = my_rtree_helper.check_box_intersection(view_box= view_rect_bounds)
    
    if all_existing_op_ints_in_area:
        for flight_details in all_existing_op_ints_in_area:            
            flight_id =  flight_details['flight_id']
            op_int_details_key = 'flight_opint.'+ flight_id
            
            op_int_details = r.get(op_int_details_key)
            
            if op_int_details:                
                my_scd_dss_helper = dss_scd_helper.SCDOperations()
                op_int_detail_raw = op_int_details.decode()
                op_int_detail = json.loads(op_int_detail_raw)                
                ovn = op_int_detail['success_response']['operational_intent_reference']['ovn']
                opint_id = op_int_detail['success_response']['operational_intent_reference']['id']
                ovn_opint = {'ovn_id':ovn,'opint_id':opint_id}              
                logger.info("Deleting operational intent {opint_id} with ovn {ovn_id}".format(**ovn_opint))

                my_scd_dss_helper.delete_operational_intent(operational_intent_id=opint_id, ovn= ovn)
        clear_area_status = ClearAreaResponse(success=True, message="All operational intents in the area cleared successfully", timestamp=arrow.now().isoformat())

    else:
        clear_area_status = ClearAreaResponse(success=True, message="All operational intents in the area cleared successfully", timestamp=arrow.now().isoformat())
   
    my_rtree_helper.clear_rtree_index()
    return JsonResponse(json.loads(json.dumps(clear_area_status, cls=EnhancedJSONEncoder)), status=200)

@api_view(['PUT','DELETE'])
@requires_scopes(['utm.inject_test_data'])
def SCDAuthTest(request, flight_id):
    
    if request.method == "PUT":
        failed_test_injection_response = TestInjectionResult(result = "Failed", notes="Processing of operational intent has failed",operational_intent_id ="")        
        rejected_test_injection_response = TestInjectionResult(result = "Rejected", notes="An existing operational intent already exists and conflicts in space and time",operational_intent_id="")
        planned_test_injection_response = TestInjectionResult(result = "Planned", notes="Successfully created operational intent in the DSS",operational_intent_id ="")
        conflict_with_flight_test_injection_response = TestInjectionResult(result = "ConflictWithFlight", notes="Processing of operational intent has failed, flight not deconflicted",operational_intent_id ="")        

        scd_test_data = request.data
        r = get_redis()
        my_rtree_helper = rtree_helper.OperationalIntentsIndexFactory(index_name=INDEX_NAME)
        my_rtree_helper.generate_operational_intents_index()
        try:
            flight_authorization_data = scd_test_data['flight_authorisation']
            f_a = FlightAuthorizationDataPayload(uas_serial_number = flight_authorization_data['uas_serial_number'],operation_category = flight_authorization_data['operation_category'], operation_mode = flight_authorization_data['operation_mode'], uas_class = flight_authorization_data['uas_class'], identification_technologies = flight_authorization_data['identification_technologies'],connectivity_methods = flight_authorization_data['connectivity_methods'],  endurance_minutes = flight_authorization_data['endurance_minutes'], emergency_procedure_url = flight_authorization_data['emergency_procedure_url'],operator_id = flight_authorization_data['operator_id'])
        except KeyError as ke:
            return Response({"result":"Could not parse test injection payload, expected key %s not found " % ke }, status = status.HTTP_400_BAD_REQUEST)
                        
        now = arrow.now()

        one_minute_from_now = now.shift(minutes=1)
        one_minute_from_now_str = one_minute_from_now.isoformat()
        two_minutes_from_now = now.shift(minutes=2)
        two_minutes_from_now_str = two_minutes_from_now.isoformat()
        opint_subscription_end_time = timedelta(seconds=60)
        try:
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
                    
                altitude_lower = Altitude(value = volume['volume']['altitude_lower']['value'],reference= volume['volume']['altitude_lower']['reference'], units =volume['volume']['altitude_lower']['units'])
                altitude_upper = Altitude(value = volume['volume']['altitude_upper']['value'],reference=  volume['volume']['altitude_upper']['reference'], units =volume['volume']['altitude_upper']['units'])                        
                volume3D = Volume3D(outline_circle=outline_circle, outline_polygon=outline_polygon, altitude_lower = altitude_lower, altitude_upper= altitude_upper)


                time_start = Time(format = volume['time_start']['format'], value = volume['time_start']['value'])
                time_end = Time(format =volume['time_end']['format'] , value = volume['time_end']['value'])

                
                volume4D = Volume4D(volume=volume3D, time_start=time_start, time_end=time_end)
                all_volumes.append(volume4D)
                
            
            operational_intent_data = OperationalIntentTestInjection(volumes = all_volumes, priority = operational_intent['priority'], off_nominal_volumes = operational_intent['off_nominal_volumes'], state = operational_intent['state'])   
            # convert operational intent to GeoJSON and get bounds
        except KeyError as ke:
            return Response({"result":"Could not parse test injection payload, expected key %s not found " % ke }, status = status.HTTP_400_BAD_REQUEST)

        test_injection_data = SCDTestInjectionDataPayload(operational_intent= operational_intent_data, flight_authorisation= f_a)

        my_geo_json_converter = dss_scd_helper.VolumesConverter()
        my_geo_json_converter.convert_volumes_to_geojson(volumes = all_volumes)
        view_rect_bounds = my_geo_json_converter.get_bounds()
                    
        # Check flight auth data first before going to DSS
        my_serial_number_validator = UAVSerialNumberValidator(serial_number = flight_authorization_data['uas_serial_number'])
        my_reg_number_validator = OperatorRegistrationNumberValidator(operator_registration_number = flight_authorization_data['operator_id'])

        is_serial_number_valid = my_serial_number_validator.is_valid()
        is_reg_number_valid = my_reg_number_validator.is_valid()
            
        if not is_serial_number_valid:
            injection_response = asdict(rejected_test_injection_response)
            return Response(json.loads(json.dumps(injection_response, cls=EnhancedJSONEncoder)), status = status.HTTP_200_OK)
        
        if not is_reg_number_valid:            
            injection_response = asdict(rejected_test_injection_response)
            return Response(json.loads(json.dumps(injection_response, cls=EnhancedJSONEncoder)), status = status.HTTP_200_OK)

        # flight authorisation data is correct, can submit the operational intent to the DSS
        all_existing_op_ints_in_area = my_rtree_helper.check_box_intersection(view_box= view_rect_bounds)
        # self_deconflicted = False if operational_intent['priority'] == 0 else True
        
        # if all_existing_op_ints_in_area and self_deconflicted == False:
        #     # there are existing op_ints in the area. 
        #     deconflicted_status = []
        #     for existing_op_int in all_existing_op_ints_in_area:                
        #         # check if start time or end time is between the existing bounds
        #         is_start_within = dss_scd_helper.is_time_within_time_period(start_time=arrow.get(existing_op_int['start_time']).datetime, end_time= arrow.get(existing_op_int['end_time']).datetime, time_to_check=arrow.get(time_start).datetime)
        #         is_end_within = dss_scd_helper.is_time_within_time_period(start_time=arrow.get(existing_op_int['start_time']).datetime, end_time= arrow.get(existing_op_int['end_time']).datetime, time_to_check=two_minutes_from_now.datetime)

        #         timeline_status = [is_end_within, is_end_within]
        
        #         if all(timeline_status):      
        #             deconflicted_status.append(True)
        #         else:
        #             deconflicted_status.append(False)
            
        #     self_deconflicted = all(deconflicted_status)
        # else:
        #     # No existing op ints we can plan it.             
        #     self_deconflicted = True
        
        my_rtree_helper.clear_rtree_index()            
        # if self_deconflicted: 
        
        my_scd_dss_helper = dss_scd_helper.SCDOperations()
        op_int_submission = my_scd_dss_helper.create_operational_intent_reference(state = operational_intent_data.state, volumes = operational_intent_data.volumes, off_nominal_volumes = operational_intent_data.off_nominal_volumes, priority = operational_intent_data.priority)
        if op_int_submission.status == "success":                
            view_r_bounds = ",".join(map(str,view_rect_bounds))
            operational_intent_full_details = OperationalIntentStorage(bounds=view_r_bounds, start_time=one_minute_from_now_str, end_time=two_minutes_from_now_str, alt_max=50, alt_min=25, success_response = op_int_submission.dss_response, operational_intent_details= operational_intent_data)
            # Store flight ID 
            flight_opint = 'flight_opint.' + str(flight_id)
            r.set(flight_opint, json.dumps(asdict(operational_intent_full_details)))
            r.expire(name = flight_opint, time = opint_subscription_end_time)

            # Store the details of the operational intent reference
            flight_op_int_storage = SuccessfulOperationalIntentFlightIDStorage(flight_id=str(flight_id), operational_intent_id=operational_intent_data.off_nominal_volumes)
            
            opint_flightref = 'opint_flightref.' + op_int_submission.operational_intent_id                
            r.set(opint_flightref, json.dumps(asdict(flight_op_int_storage)))
            r.expire(name = opint_flightref, time = opint_subscription_end_time)
            
            planned_test_injection_response.operational_intent_id = op_int_submission.operational_intent_id
        elif op_int_submission.status=='conflict_with_flight':
            conflict_with_flight_test_injection_response.operational_intent_id = op_int_submission.operational_intent_id
            return Response(json.loads(json.dumps(conflict_with_flight_test_injection_response, cls=EnhancedJSONEncoder)), status = status.HTTP_200_OK)
        else: 
            failed_test_injection_response.operational_intent_id = op_int_submission.operational_intent_id
            return Response(json.loads(json.dumps(failed_test_injection_response, cls=EnhancedJSONEncoder)), status = status.HTTP_200_OK)
        # else:
        #     tmp_operational_intent_id = str(uuid.uuid4())
        #     rejected_test_injection_response.operational_intent_id = tmp_operational_intent_id
        #     return Response(json.loads(json.dumps(rejected_test_injection_response, cls=EnhancedJSONEncoder)), status = status.HTTP_200_OK)
        
        try: 
            injection_response = asdict(planned_test_injection_response)  
                 
            return Response(json.loads(json.dumps(injection_response, cls=EnhancedJSONEncoder)), status = status.HTTP_200_OK)
        except KeyError as ke:            
            injection_response = asdict(failed_test_injection_response)            
            return Response(json.loads(json.dumps(injection_response, cls=EnhancedJSONEncoder)), status = status.HTTP_400_BAD_REQUEST)

    elif request.method == "DELETE":        
        
        r = get_redis()    
        op_int_details_key = 'flight_opint.'+ str(flight_id)
        op_int_details = r.get(op_int_details_key)   
        
        if op_int_details:                
            my_scd_dss_helper = dss_scd_helper.SCDOperations()
            op_int_detail_raw = op_int_details.decode()
            op_int_detail = json.loads(op_int_detail_raw)                
            ovn = op_int_detail['success_response']['operational_intent_reference']['ovn']
            opint_id = op_int_detail['success_response']['operational_intent_reference']['id']
            ovn_opint = {'ovn_id':ovn,'opint_id':opint_id}              
            logger.info("Deleting operational intent {opint_id} with ovn {ovn_id}".format(**ovn_opint))
            my_scd_dss_helper.delete_operational_intent(operational_intent_id=opint_id, ovn= ovn)
            r.delete(op_int_details)

            delete_flight_response = DeleteFlightResponse(result="Closed", notes="The flight was closed successfully by the USS and is now out of the UTM system.")
        else:
            delete_flight_response = DeleteFlightResponse(result="Failed", notes="The flight was not found in the USS, please check your flight ID %s" % flight_id)


        return Response(json.loads(json.dumps(delete_flight_response, cls=EnhancedJSONEncoder)), status = status.HTTP_200_OK)