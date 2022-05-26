from re import I
import redis

import logging
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
logger = logging.getLogger('django')

from os import environ as env

def get_redis():
    # A method to get global redis instance 
    redis_host = env.get('REDIS_HOST', "redis")
    redis_port = env.get('REDIS_PORT', 6379)
    redis_password = env.get('REDIS_Password', None)
    
    if redis_password:
        r = redis.Redis(host=redis_host, port=redis_port, password = redis_password, decode_responses=True)
    else:
        r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

    return r
