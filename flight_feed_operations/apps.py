# my_app/apps.py

from django.apps import AppConfig
from flight_feed_operations import flight_stream_helper


class MyAppConfig(AppConfig):
    name = 'flight_feed_operations'
    def ready(self):
        my_stream_ops = flight_stream_helper.StreamHelperOps()
        my_stream_ops.create_pull_cg()    
        print("Created PULL CG...")  
        my_stream_ops.create_read_cg()    
        print("Created READ CG...")   

