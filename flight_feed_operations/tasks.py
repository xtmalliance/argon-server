from celery.decorators import task
import os, json
import logging
import requests
from . import flight_stream_helper
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

#### Airtraffic Endpoint

@task(name='write_incoming_air_traffic_data')
def write_incoming_air_traffic_data(observation): 
    obs = json.loads(observation)
    my_stream_ops = flight_stream_helper.StreamHelperOps()
    all_observations = my_stream_ops.get_push_stream()       
    msg_id = all_observations.add(obs)       
    
    return msg_id


# @celery.task()
# def print_hello():
#     dir(app)
    
#     with app.app_context():
#         cg = app.get_push_stream()

#     logger = print_hello.get_logger()

#     logger.info("Hello")
    
# This method submits flight information to Spotlight
@task(name='submit_flights_to_spotlight')
def submit_flights_to_spotlight():
    # get existing consumer group
    my_cg_ops = flight_stream_helper.StreamHelperOps()
    all_observations = my_cg_ops.get_push_stream()
    messages = all_observations.read()
    pending_messages = []
    
    my_credentials = flight_stream_helper.PassportCredentialsGetter()
    credentials = my_credentials.get_cached_credentials()
    if 'error' in credentials: 
        logging.error('Error in getting credentials %s' % credentials)
    else:
        for message in messages:             
            pending_messages.append({'timestamp': message.timestamp,'seq': message.sequence, 'msg_data':message.data, 'address':message.data['icao_address']})
        
        # sort by date
        pending_messages.sort(key=lambda item:item['timestamp'], reverse=True)

        # Keep only the latest message
        distinct_messages = {i['address']:i for i in reversed(pending_messages)}.values()
        FLIGHT_SPOTLIGHT_URL = os.getenv('FLIGHT_SPOTLIGHT_URL', 'http://localhost:5000')
        
        securl = FLIGHT_SPOTLIGHT_URL + '/set_air_traffic'

        headers = {"Authorization": "Bearer " + credentials['access_token']}
        for message in distinct_messages:
            
            payload = {"icao_address" : message['address'],"traffic_source" :message['msg_data']['traffic_source'], "source_type" : message['msg_data']['source_type'], "lat_dd" : message['msg_data']['lat_dd'], "lon_dd" : message['msg_data']['lon_dd'], "time_stamp" : message['timestamp'],"altitude_mm" : message['msg_data']['altitude_mm'], "metadata": message['msg_data']['metadata']}
            response = requests.post(securl, data= payload, headers=headers)
            
            logging.info(response.status_code)
