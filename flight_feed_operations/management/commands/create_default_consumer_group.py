from django.core.management.base import BaseCommand, CommandError
from flight_feed_operations import flight_stream_helper

class Command(BaseCommand):
    help = "Create a consumer group once"

    def handle(self, *args, **options):
        myCGOps = flight_stream_helper.ConsumerGroupOps()
        cg = myCGOps.create_cg()     

