import plcnxdb.settings 
from celery.decorators import task
from celery.utils.log import get_task_logger
import logging
import dss_rw_helper


@task('SubmitDSSSubscription')
def submit_dss_subscription(view , vertex_list):
    myDSSSubscriber = dss_rw_helper.RemoteIDOperations()
    subscription_created = myDSSSubscriber.create_dss_subscription(vertex_list = vertex_list, view_port = view)
    logging.success("Created Subscription %s" subscription_created.id)