from django.core.management.base import BaseCommand, CommandError
from os import environ as env
from common.database_operations import BlenderDatabaseReader
from common.data_definitions import OPERATION_STATES
import arrow
from dotenv import load_dotenv, find_dotenv
import logging
from auth_helper.common import get_redis
import json
from scd_operations.dss_scd_helper import SCDOperations
from scd_operations.scd_data_definitions import Time, OperationalIntentReferenceDSSResponse


load_dotenv(find_dotenv())
 
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

logger = logging.getLogger('django')

class Command(BaseCommand):
    
    help = 'This command clears the operation in the DSS after the state has been set to ended.'

    def add_arguments(self, parser):

        parser.add_argument(
        "-d",
        "--flight_declaration_id",
        dest = "flight_declaration_id",
        metavar = "ID of the flight declaration",
        help='Specify the ID of Flight Declaration')

        parser.add_argument(
        "-d",
        "--dryrun",
        dest = "dryrun",
        metavar = "Set if this is a dry run",
        default= '1', 
        help='Set if it is a dry run')
        
        
    def handle(self, *args, **options):
        dry_run = options['dryrun']                 
        dry_run = 1 if dry_run =='1' else 0

        new_state = OPERATION_STATES[2][1]
        
        try:        
            flight_declaration_id = options['flight_declaration_id']
        except Exception as e:
            raise CommandError("Incomplete command, Flight Declaration ID not provided %s"% e)

        # Get the flight declaration

        my_database_reader = BlenderDatabaseReader()
        now = arrow.now().isoformat()

        flight_declaration = my_database_reader.get_flight_declaration_by_id(flight_declaration_id= flight_declaration_id)
        if not flight_declaration: 
            raise CommandError("Flight Declaration with ID {flight_declaration_id} does not exist".format(flight_declaration_id = flight_declaration_id))

        my_scd_dss_helper = SCDOperations()
        flight_authorization = my_database_reader.get_flight_authorization_by_flight_declaration(flight_declaration_id=flight_declaration_id)
        if not dry_run: 
            operational_intent_id = flight_authorization.operational_intent_id
                    
            r = get_redis()    
            
            opint_flightref = 'opint_flightref.' + str(operational_intent_id)
            
            if r.exists(opint_flightref):
                opint_ref_raw = r.get(opint_flightref)
                opint_ref = json.loads(opint_ref_raw)
                flight_id = opint_ref['flight_id']
                flight_opint = 'flight_opint.' + flight_id   
                    
            if r.exists(flight_opint):
                op_int_details_raw = r.get(flight_opint)
                op_int_details = json.loads(op_int_details_raw)
                
                reference_full = op_int_details['success_response']['operational_intent_reference']
                details_full = op_int_details['operational_intent_details']
                # Load existing opint details

                stored_operational_intent_id= reference_full['id']
                stored_manager = reference_full['manager']
                stored_uss_availability = reference_full['uss_availability']
                stored_version = reference_full['version']
                stored_state = reference_full['state']
                stored_ovn = reference_full['ovn']
                stored_uss_base_url = reference_full['uss_base_url']
                stored_subscription_id = reference_full['subscription_id']
                
                stored_time_start = Time(format=reference_full['time_start']['format'], value=reference_full['time_start']['value'])
                stored_time_end = Time(format=reference_full['time_end']['format'], value=reference_full['time_end']['value'])

                stored_volumes = details_full['volumes']
                stored_priority = details_full['priority']
                stored_off_nominal_volumes = details_full['off_nominal_volumes']

                reference = OperationalIntentReferenceDSSResponse(id=stored_operational_intent_id, manager =stored_manager, uss_availability= stored_uss_availability, version= stored_version, state= stored_state, ovn =stored_ovn, time_start= stored_time_start, time_end = stored_time_end, uss_base_url=stored_uss_base_url, subscription_id=stored_subscription_id)

                    
                extents = flight_declaration.extent
                
                operational_update_response = my_scd_dss_helper.update_specified_operational_intent_referecnce(operational_intent_id = operational_intent_id,extents= extents new_state= new_state, )




            if operational_update_response.status == 200:
                logging.info("Successfully removed operational intent {operational_intent_id} from DSS".format(operational_intent_id = operational_intent_id))
            else: 
                logging.info("Error in deleting operational intent from DSS")

        else: 
                logging.info("Error in transitioning {flight_declaration_id} for removal from DSS".format(flight_declaration_id = flight_declaration_id))
