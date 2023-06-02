from django.core.management.base import BaseCommand, CommandError
from conformance_monitoring_operations.tasks import check_flight_conformance

class Command(BaseCommand):
    help = "Check conformance of existing operations"

    def handle(self, *args, **options):
        check_flight_conformance.delay()