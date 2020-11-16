import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

REDIS_HOST = os.getenv('REDIS_HOST',"redis")
REDIS_PORT = 6379
BROKER_URL = os.getenv('REDIS_URL', "redis://{host}:{port}/0".format(
    host=REDIS_HOST, port=str(REDIS_PORT)))

CELERY_RESULT_BACKEND = BROKER_URL