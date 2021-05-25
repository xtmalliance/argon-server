from celery.decorators import task
from celery.utils.log import get_task_logger
import logging
from . import dss_rw_helper
from walrus import Database
from flight_feed_operations import flight_stream_helper
from dotenv import load_dotenv, find_dotenv
import tldextract
import json
from os import environ as env
from datetime import datetime, timedelta, timezone
import redis
import requests
load_dotenv(find_dotenv())
 

@task(name='submit_dss_subscription')
def submit_dss_subscription(view , vertex_list, request_uuid):
    myDSSSubscriber = dss_rw_helper.RemoteIDOperations()
    subscription_created = myDSSSubscriber.create_dss_subscription(vertex_list = vertex_list, view_port = view, request_uuid = request_uuid)
    logging.success("Subscription creation status: %s" % subscription_created['created'])


def get_all_observations_group(create=False):
    
    db = Database(host=env.get("REDIS_HOST"), port=env.get("REDIS_PORT"))   
    stream_keys = ['all_observations']
    
    cg = db.time_series('cg-obs', stream_keys)
    if create:
        for stream in stream_keys:
            db.xadd(stream, {'data': ''})

    if create:
        cg.create()
        cg.set_id('$')

    return cg.all_observations



@task(name='poll_uss_for_flights')
def poll_uss_for_flights():
    authority_credentials = dss_rw_helper.AuthorityCredentialsGetter()
    redis = redis.Redis(host=env.get('REDIS_HOST',"redis"), port =env.get('REDIS_PORT',6379))   
    flights_dict = redis.hgetall("all_uss_flights")
    all_flights_url = flights_dict['all_flights_url']
    # flights_view = flights_dict['view']
    cg_ops = flight_stream_helper.ConsumerGroupOps()
    cg = cg_ops.get_all_observations_group()

    for cur_flight_url in all_flights_url:
        ext = tldextract.extract(cur_flight_url)          
        audience = '.'.join(ext[:3]) # get the subdomain, domain and suffix and create a audience and get credentials
        auth_credentials = authority_credentials.get_cached_credentials(audience)

        headers = {'content-type': 'application/json', 'Authorization': 'Bearer ' + auth_credentials}
    
        flights_response = requests.get(cur_flight_url, headers=headers)
        if flights_response.status_code == 200:
            # https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/uastech/standards/astm_rid_1.0/remoteid/canonical.yaml#tag/p2p_rid/paths/~1v1~1uss~1flights/get
            all_flights = flights_response['flights']
            for flight in all_flights:
                flight_id = flight['id']
                try: 
                    assert flight.get('current_state') is not None
                except AssertionError as ae:
                    logging.error('There is no current_state provided by SP on the flights url %s' % cur_flight_url)
                    logging.debug(json.dumps(flight))
                else:
                    flight_current_state = flight['current_state']
                    position = flight_current_state['position']
                    flight_metadata = {'id':flight_current_state['id'],"aircraft_type":flight_current_state["aircraft_type"]}
                    now  = datetime.now()
                    time_stamp =  now.replace(tzinfo=timezone.utc).timestamp()
                    
                    if {"lat", "lng", "alt"} <= position.keys():
                        # check if lat / lng / alt existis
                        single_observation = {"icao_address" : flight_id,"traffic_source" :1, "source_type" : 1, "lat_dd" : position['lat'], "lon_dd" : position['lng'], "time_stamp" : time_stamp,"altitude_mm" : position['alt'],'metadata':json.dumps(flight_metadata)}
                        # write incoming data directly
                        
                        cg.add(single_observation)    
                    else: 
                        logging.error("Error in received flights data: %{url}s ".format(**flight) ) 
                
        else:
            logging.info(flights_response.status_code) 
