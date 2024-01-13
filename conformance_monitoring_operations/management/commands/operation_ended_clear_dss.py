import json
import logging

import arrow
from django.core.management.base import BaseCommand, CommandError
from dotenv import find_dotenv, load_dotenv

from auth_helper.common import get_redis
from common.database_operations import BlenderDatabaseReader
from scd_operations.dss_scd_helper import SCDOperations

load_dotenv(find_dotenv())

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

logger = logging.getLogger("django")


class Command(BaseCommand):
    help = "This command clears the operation in the DSS after the state has been set to ended."

    def add_arguments(self, parser):
        parser.add_argument(
            "-o",
            "--flight_declaration_id",
            dest="flight_declaration_id",
            metavar="ID of the flight declaration",
            help="Specify the ID of Flight Declaration",
        )

        parser.add_argument(
            "-d",
            "--dry_run",
            dest="dry_run",
            metavar="Set if this is a dry run",
            default="1",
            help="Set if it is a dry run",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        dry_run = 1 if dry_run == "1" else 0

        my_scd_dss_helper = SCDOperations()
        my_database_reader = BlenderDatabaseReader()
        now = arrow.now().isoformat()

        try:
            flight_declaration_id = options["flight_declaration_id"]
        except Exception as e:
            raise CommandError("Incomplete command, Flight Declaration ID not provided %s" % e)

        flight_declaration = my_database_reader.get_flight_declaration_by_id(flight_declaration_id=flight_declaration_id)
        if not flight_declaration:
            raise CommandError(
                "Flight Declaration with ID {flight_declaration_id} does not exist".format(flight_declaration_id=flight_declaration_id)
            )
        flight_authorization = my_database_reader.get_flight_authorization_by_flight_declaration_obj(flight_declaration=flight_declaration)
        dss_operational_intent_ref_id = flight_authorization.dss_operational_intent_id

        r = get_redis()

        flight_opint = "flight_opint." + str(flight_declaration_id)

        if r.exists(flight_opint):
            op_int_details_raw = r.get(flight_opint)
            op_int_details = json.loads(op_int_details_raw)
            reference_full = op_int_details["success_response"]["operational_intent_reference"]
            stored_ovn = reference_full["ovn"]
            try:
                flight_declaration_id = options["flight_declaration_id"]
            except Exception as e:
                raise CommandError("Incomplete command, Flight Declaration ID not provided %s" % e)

            # Get the flight declaration

            my_database_reader = BlenderDatabaseReader()
            flight_declaration = my_database_reader.get_flight_declaration_by_id(flight_declaration_id=flight_declaration_id)
            if not flight_declaration:
                raise CommandError(
                    "Flight Declaration with ID {flight_declaration_id} does not exist".format(flight_declaration_id=flight_declaration_id)
                )

            flight_authorization = my_database_reader.get_flight_authorization_by_flight_declaration(flight_declaration_id=flight_declaration_id)
            if not dry_run:
                operation_removal_status = my_scd_dss_helper.delete_operational_intent(
                    dss_operational_intent_ref_id=dss_operational_intent_ref_id,
                    ovn=stored_ovn,
                )
                if operation_removal_status.status == 200:
                    logger.info(
                        "Successfully removed operational intent {dss_operational_intent_ref_id} from DSS".format(
                            dss_operational_intent_ref_id=dss_operational_intent_ref_id
                        )
                    )
                else:
                    logger.info("Error in deleting operational intent from DSS")

            else:
                logger.info("Error in removing {flight_declaration_id} reference  from DSS".format(flight_declaration_id=flight_declaration_id))
