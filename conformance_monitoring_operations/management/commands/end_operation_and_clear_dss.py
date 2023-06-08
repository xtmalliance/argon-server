from django.core.management.base import BaseCommand, CommandError
from os import environ as env
from common.database_operations import BlenderDatabaseReader
import arrow
from conformance_monitoring_operations.operation_state_helper import AcceptedState, ActivatedState, EndedState, NonconformingState, ContingentState, FlightOperationStateMachine, match_state, get_status
from uss_operations.uss_flight_operations import DSSFlightOperations
from dotenv import load_dotenv, find_dotenv
import logging
from scd_operations.dss_scd_helper import SCDOperations

load_dotenv(find_dotenv())
 
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

logger = logging.getLogger('django')

class Command(BaseCommand):
    
    help = 'End operation and clear dss'

    def add_arguments(self, parser):

        parser.add_argument(
        "-d",
        "--flightdeclarationid",
        dest = "flightdeclarationid",
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

        # This is the event that triggers the change of state     
        event = 'operator_confirms_ended'
        
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

        # get current state of the operation
        current_state_int = flight_declaration.state
        current_state = match_state(current_state_int)

        my_operation_state_machine =FlightOperationStateMachine(state = current_state)
        my_operation_state_machine.on_event(event)
        new_state = get_status(my_operation_state_machine.state)
        if dry_run: 
            logging.info("Saving new state")
        else:
            # Set state as ended 
            flight_declaration.state = new_state
            flight_declaration.save()
            

        my_scd_dss_helper = SCDOperations()
        flight_authorization = my_database_reader.get_flight_authorization_by_flight_declaration(flight_declaration_id=flight_declaration_id)
        if not dry_run: 
            operational_intent_id = flight_authorization.operational_intent_id
            operation_removal_status = my_scd_dss_helper.delete_operational_intent(operational_intent_id = operational_intent_id)
            if operation_removal_status.status == 200:
                logging.info("Successfully removed operational intent {operational_intent_id} from DSS".format(operational_intent_id = operational_intent_id))
            else: 
                logging.info("Error in deleting operational intent from DSS")

        else: 
            logging.info("Submitting {flight_declaration_id} for removal from DSS".format(flight_declaration_id = flight_declaration_id))






