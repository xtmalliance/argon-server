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
    myDSSSubscriber = dss_rw_helper.RemoteIDOperations()
    subscription_created = myDSSSubscriber.create_dss_subscription(vertex_list = vertex_list, view_port = view, request_uuid = request_uuid)
    logging.success("Subscription creation status: %s" % subscription_created['created'])

@task(name='poll_uss_for_flights_async')
def poll_uss_for_flights_async():
    myDSSSubscriber = dss_rw_helper.RemoteIDOperations()

    cg_ops = flight_stream_helper.ConsumerGroupOps()
    cg = cg_ops.get_push_pull_stream()

    # TODO: Get existing flight details from subscription
    redis = redis.Redis(host=env.get('REDIS_HOST',"redis"), port =env.get('REDIS_PORT',6379))   
    flights_dict = {}
    # Get the flights URL from the DSS and put it in 
    for keybatch in flight_stream_helper.batcher(redis.scan_iter('all_uss_flights-*'),500): # reasonably we wont have more than 500 subscriptions active
        flights_dict = redis.get(*keybatch)
        myDSSSubscriber.query_uss_for_rid(flights_dict, cg])