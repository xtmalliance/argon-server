from celery.decorators import task
import logging
from . import dss_rw_helper

@task(name='submit_dss_subscription')
def submit_dss_subscription(view , vertex_list, request_uuid):
    myDSSSubscriber = dss_rw_helper.RemoteIDOperations()
    subscription_created = myDSSSubscriber.create_dss_subscription(vertex_list = vertex_list, view_port = view, request_uuid = request_uuid)
    logging.success("Subscription creation status: %s" % subscription_created['created'])

@task(name='poll_uss_for_flights_async')
def poll_uss_for_flights_async():
    myDSSSubscriber = dss_rw_helper.RemoteIDOperations()

    # Get existing flight details from subscription
    flights_dict = {}

    myDSSSubscriber.query_uss_for_rid(flights_dict)