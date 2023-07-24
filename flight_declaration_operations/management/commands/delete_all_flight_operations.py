from django.core.management.base import BaseCommand, CommandError
from flight_declaration_operations.models import FlightDeclaration
from common.database_operations import BlenderDatabaseReader
from scd_operations import dss_scd_helper
class Command(BaseCommand):
    help = 'This command delete.'

    def add_arguments(self, parser):

        parser.add_argument(
        "-d",
        "--dry_run",
        dest = "dry_run",
        metavar = "Set if this is a dry run",
        default = '1', 
        help ='Set if it is a dry run')
        
        parser.add_argument(
        "-s",
        "--dss",
        dest = "dss",
        metavar = "Specify if the operational intents should also be removed from the DSS",
        default = 1,         
        type = int, 
        help ='Set if it is a dry run')


    def handle(self, *args, **options):
        
        dry_run = options['dry_run']                 
        clear_dss = options['dss']    
        dry_run = 1 if dry_run =='1' else 0
        my_database_reader = BlenderDatabaseReader()
        all_operations = my_database_reader.get_all_flight_declarations()
        for o in all_operations:
            f_a = my_database_reader.get_flight_authorization_by_flight_declaration_obj(flight_declaration=o)
            if dry_run: 
                print("Dry Run : Deleting operation %s"% a.id)
            else:
                print("Deleting operation %s..."% a.id)
                if clear_dss:
                    if f_a:
                        dss_op_int_id = f_a.dss_operational_intent_id
                        print("Clearing operational intent id  %s in the DSS..."% dss_op_int_id)
                        my_scd_dss_helper = dss_scd_helper.SCDOperations()
                        my_scd_dss_helper.delete_operational_intent(operational_intent_id = dss_op_int_id)
                o.delete()
