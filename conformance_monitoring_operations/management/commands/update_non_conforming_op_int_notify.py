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
        
    help = 'This command takes in a flight declaration: and A) declares it as non-conforming, B) creates off-nominal volumes C) Updates the DSS with the new status D) Notifies Peer USS '

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
        