# from celery.schedules import crontab
from datetime import timedelta
import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

HEARTBEAT = os.getenv('HEARTBEAT_RATE_SECS',5)
CELERY_IMPORTS = ('blender.tasks.blend')
CELERY_TASK_RESULT_EXPIRES = 30
CELERY_TIMEZONE = 'UTC'

CELERY_ACCEPT_CONTENT = ['json', 'msgpack', 'yaml']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

CELERYBEAT_SCHEDULE = {
    'submit-spotlight': {
        'task': 'blender.tasks.blend.submit_flights_to_spotlight',
        # Every 30 secionds
        'schedule': timedelta(seconds=int(HEARTBEAT)),
    }, 
    
    # 'poll-flights':{
    #     'task': 'blender.tasks.flights_reader.poll_uss_for_flights',
    #     # Every 30 secionds
    #     'schedule': timedelta(seconds=int(HEARTBEAT)),
        
    # }
}