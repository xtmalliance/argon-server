# my_app/apps.py

from django.apps import AppConfig
from flight_feed_operations import flight_stream_helper


class MyAppConfig(AppConfig):
    name = 'flight_feed_operations'
    def ready(self):
        
        myCGOps = flight_stream_helper.ConsumerGroupOps()
        cg = myCGOps.get_push_pull_stream()     

