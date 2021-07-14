from celery.decorators import task
import logging
from . import dss_rw_helper
import redis
from os import environ as env
from flight_feed_operations import flight_stream_helper
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

@task(name='submit_dss_subscription')
def submit_dss_subscription(view , vertex_list, request_uuid):
    subscription_time_delta = 30
    myDSSSubscriber = dss_rw_helper.RemoteIDOperations()
    subscription_created = myDSSSubscriber.create_dss_subscription(vertex_list = vertex_list, view_port = view, request_uuid = request_uuid,subscription_time_delta=subscription_time_delta)
    logging.success("Subscription creation status: %s" % subscription_created['created'])

@task(name='poll_uss_for_flights_async')
def poll_uss_for_flights_async():
    myDSSSubscriber = dss_rw_helper.RemoteIDOperations()

    stream_ops = flight_stream_helper.StreamHelperOps()
    push_cg = stream_ops.get_push_cg()
    all_observations = push_cg.all_observations

    # TODO: Get existing flight details from subscription
    r = redis.Redis(host=env.get('REDIS_HOST',"redis"), port =env.get('REDIS_PORT',6379), decode_responses=True)
    flights_dict = {}
    # Get the flights URL from the DSS and put it in 
    for keybatch in flight_stream_helper.batcher(r.scan_iter('all_uss_flights:*'), 100): # reasonably we wont have more than 100 subscriptions active        
        key_batch_set = set(keybatch)        
        for key in key_batch_set:
            if key:
                flights_dict = r.hgetall(key)      
                logging.debug('Flights Dict %s' % flights_dict)    
                if bool(flights_dict):
                    subscription_id = key.split(':')[1]                    
                    myDSSSubscriber.query_uss_for_rid(flights_dict, all_observations,subscription_id)