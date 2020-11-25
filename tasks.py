import celery
import requests
from app import celery
from geo_fence_ops import geo_fence_writer
from flight_declaration_ops import flight_declaration_writer
from flask import Flask, url_for, current_app
from stream_helper import ConsumerGroupOps
from dss_ops import rid_dss_operations


#### Airtraffic Endpoint
@celery.task()
def write_incoming_data(observation): 
    myCGOps = ConsumerGroupOps()
    cg = myCGOps.get_consumer_group()           
    msgid = cg.add(observation)            
    return msgid


@celery.task()
def write_geo_fence(geo_fence): 
    my_credentials = geo_fence_writer.PassportCredentialsGetter()
    gf_credentials = my_credentials.get_cached_credentials()
    
    try: 
        assert any(gf_credentials) == True # Credentials dictionary is populated
    except AssertionError as ae: 
        # Error in getting a Geofence credentials getting
        current_app.logger.error('Error in getting Flight Declaration Token')
        current_app.logger.error(ae)

    # my_uploader = geo_fence_writer.GeoFenceUploader(credentials = gf_credentials)
    # upload_status = my_uploader.upload_to_server(gf=geo_fence)
    # print(upload_status)
    # current_app.logger.info(upload_status)

@celery.task()
def write_flight_declaration(fd):   
    my_credential_ops = flight_declaration_writer.PassportCredentialsGetter()        
    fd_credentials = my_credential_ops.get_cached_credentials()
    
    try: 
        assert any(fd_credentials) == True # Dictionary is populated 
    except AssertionError as e: 
        # Error in receiving a Flight Declaration credential
        current_app.logger.error('Error in getting Flight Declaration Token')
        current_app.logger.error(e)
    else:    
        my_uploader = flight_declaration_writer.FlightDeclarationsUploader(credentials = fd_credentials)
        my_uploader.upload_to_server(flight_declaration_json=fd)
 
@celery.task()
def submit_dss_subscription(view , vertex_list):
    myDSSSubscriber = rid_dss_operations.RemoteIDOperations()
    subscription_created = myDSSSubscriber.create_dss_subscription(vertex_list = vertex_list, view_port = view)