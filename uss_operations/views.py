from rest_framework.decorators import api_view
from auth_helper.utils import requires_scopes
from dataclasses import asdict, is_dataclass
# Create your views here.
from os import environ as env
from dotenv import load_dotenv, find_dotenv
from uuid import UUID
from django.http import JsonResponse
from .uss_data_definitions import OperationalIntentNotFoundResponse, OperationalIntentDetails, UpdateOperationalIntent
from scd_operations.scd_data_definitions import OperationalIntentDetailsUSSResponse, OperationalIntentUSSDetails, OperationalIntentReferenceDSSResponse, Time
import json 
import logging 
import redis


load_dotenv(find_dotenv())
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

@api_view(['POST'])
@requires_scopes(['utm.strategic_coordination'])
def USSUpdateOpIntDetails(request):
    # TODO: Process changing of updated operational intent 
    updated_success = UpdateOperationalIntent(message="New or updated full operational intent information received successfully ")
    return JsonResponse(json.loads(json.dumps(updated_success, cls=EnhancedJSONEncoder)), status=204)


@api_view(['GET'])
@requires_scopes(['utm.strategic_coordination'])
def USSOpIntDetails(request, opint_id):
    r = redis.Redis(host=env.get('REDIS_HOST',"redis"), port =env.get('REDIS_PORT',6379))      

    opint_flightref = 'opint_flightref.' + str(opint_id)
    
    if r.exists(opint_flightref):
        opint_ref_raw = r.get(opint_flightref)
        opint_ref = json.loads(opint_ref_raw)
        flight_id = opint_ref['flight_id']
        flight_opint = 'flight_opint.' + flight_id                
        
        if r.exists(flight_opint):
            op_int_details_raw = r.get(flight_opint)
            op_int_details = json.loads(op_int_details_raw)
            reference_full = op_int_details['success_response']['dss_response']['operational_intent_reference']
            details_full = op_int_details['success_response']['operational_intent_details']
            # Load existing opint details

            stored_operational_intent_id= reference_full['id']
            stored_manager = reference_full['manager']
            stored_uss_availability = reference_full['uss_availability']
            stored_version = reference_full['version']
            stored_state = reference_full['state']
            stored_ovn = reference_full['ovn']
            stored_uss_base_url = reference_full['reference_full']
            stored_subscription_id = reference_full['subscription_id']
            
            stored_time_start = Time(format=reference_full['time_start']['format'], value=reference_full['time_start']['value'])
            stored_time_end = Time(format=reference_full['time_end']['format'], value=reference_full['time_end']['value'])

            stored_volumes = details_full['volumes']
            stored_priority = details_full['priority']
            stored_off_nominal_volumes = details_full['off_nominal_volumes']


            reference = OperationalIntentReferenceDSSResponse(id=stored_operational_intent_id, manager =stored_manager, uss_availability= stored_uss_availability, version= stored_version, state= stored_state, ovn =stored_ovn, time_start= stored_time_start, time_end = stored_time_end, uss_base_url=stored_uss_base_url, subscription_id=stored_subscription_id)
            details = OperationalIntentUSSDetails(volumes=stored_volumes, priority=stored_priority, off_nominal_volumes=stored_off_nominal_volumes)
            

            operational_intent = OperationalIntentDetailsUSSResponse(reference=reference, deatils=details)
            operational_intent_response = OperationalIntentDetails(operational_intent=operational_intent)

            return JsonResponse(json.loads(json.dumps(operational_intent_response, cls=EnhancedJSONEncoder)), status=200)


        else:
            not_found_response = OperationalIntentNotFoundResponse(message="Requested Operational intent with id %s not found" % str(opint_id))

            return JsonResponse(json.loads(json.dumps(not_found_response, cls=EnhancedJSONEncoder)), status=404)

    else:
        not_found_response = OperationalIntentNotFoundResponse(message="Requested Operational intent with id %s not found" % str(opint_id))

        return JsonResponse(json.loads(json.dumps(not_found_response, cls=EnhancedJSONEncoder)), status=404)
