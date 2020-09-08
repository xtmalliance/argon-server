# from celery.schedules import crontab
from datetime import timedelta


CELERY_IMPORTS = ('blender.tasks.blend')
CELERY_TASK_RESULT_EXPIRES = 30
CELERY_TIMEZONE = 'UTC'

CELERY_ACCEPT_CONTENT = ['json', 'msgpack', 'yaml']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

CELERYBEAT_SCHEDULE = {
    'test-celery': {
        'task': 'blender.tasks.blend.submit_flights_to_spotlight',
        # Every 30 secionds
        'schedule': timedelta(seconds=10),
    }
}