from django.core.management.base import BaseCommand, CommandError
from conformance_monitoring_operations.tasks import check_flight_conformance


class Command(BaseCommand):
    help = "Check conformance of existing operations"

    def add_arguments(self, parser):
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

        check_flight_conformance.delay(dry_run=dry_run)
