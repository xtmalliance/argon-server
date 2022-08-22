import redis
from walrus import Database
import logging
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
logger = logging.getLogger('django')

from os import environ as env

def get_redis():
    # A method to get the redis instance and is used globally
    redis_host = env.get('REDIS_HOST', "redis")
    redis_port = env.get('REDIS_PORT', 6379)
    redis_password = env.get('REDIS_PASSWORD', None)
    
    if redis_password:
        r = redis.Redis(host=redis_host, port=redis_port, password = redis_password, charset="utf-8",decode_responses=True)
    else:
        r = redis.Redis(host=redis_host, port=redis_port, charset="utf-8",decode_responses=True)

    return r


def get_walrus_database():

    redis_host = env.get('REDIS_HOST', "redis")
    redis_port = env.get('REDIS_PORT', 6379)
    redis_password = env.get('REDIS_PASSWORD', None)
    
    if redis_password:
        db = Database(host=redis_host, port=redis_port, password = redis_password)               
    else: 
        db = Database(host=redis_host, port=redis_port)   
    return db
        