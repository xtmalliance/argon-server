from django.core.management.base import BaseCommand, CommandError
from common.database_operations import BlenderDatabaseReader
import arrow


class Command(BaseCommand):
    help = "Check conformance based on telemetry operations"

    def add_arguments(self, parser):
        parser.add_argument(
            "-d",
            "--flightdeclarationid",
            dest="flightdeclarationid",
            metavar="ID of the flight declaration",
            help="Specify the ID of Flight Declaration",
        )

        parser.add_argument(
            "-d",
            "--dryrun",
            dest="dryrun",
            metavar="Set if this is a dry run",
            default="1",
            help="Set if it is a dry run",
        )

    def handle(self, *args, **options):
        dry_run = options["dryrun"]
        dry_run = 1 if dry_run == "1" else 0
        operation_conformant = True

        try:
            flight_declaration_id = options["flight_declaration_id"]
        except Exception as e:
            raise CommandError(
                "Incomplete command, Flight Declaration ID not provided %s" % e
            )

        my_database_reader = BlenderDatabaseReader()
        now = arrow.now().isoformat()

        flight_declaration = my_database_reader.get_flight_declaration_by_id(
            flight_declaration_id=flight_declaration_id
        )
        if not flight_declaration:
            raise CommandError(
                "Flight Declaration with ID {flight_declaration_id} does not exist".format(
                    flight_declaration_id=flight_declaration_id
                )
            )

        # get current state of the operation
        current_state_int = flight_declaration.state

        ## Conduct checks
        if operation_conformant:
            return True

        else:  # Operation is not conformant
            return False
