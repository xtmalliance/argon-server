import os, json
import logging
from .data_definitions import SingleAirtrafficObervation
import requests
import time
import arrow
import pandas as pd
from . import flight_stream_helper
from flight_blender.celery import app
from os import environ as env
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
 
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

logger = logging.getLogger('django')

#### Airtraffic Endpoint

@app.task(name='write_incoming_air_traffic_data')
def write_incoming_air_traffic_data(observation):         
    obs = json.loads(observation)    
    my_stream_ops = flight_stream_helper.StreamHelperOps()   
    cg = my_stream_ops.get_push_cg()     
    msg_id = cg.all_observations.add(obs)      
    cg.all_observations.trim(1000)
    return msg_id


# @celery.task()
# def print_hello():
#     dir(app)
    
#     with app.app_context():
#         cg = app.get_push_cg() 

#     logger = print_hello.get_logger()

#     logger.info("Hello")
    
# This method submits flight information to Spotlight
@app.task(name='submit_flights_to_spotlight')
def submit_flights_to_spotlight():
    # get existing consumer group
    my_cg_ops = flight_stream_helper.StreamHelperOps()
    push_cg = my_cg_ops.get_push_cg()
    messages = push_cg.read()
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

        logging.info(len(distinct_messages))
        FLIGHT_SPOTLIGHT_URL = os.getenv('FLIGHT_SPOTLIGHT_URL', 'http://localhost:5000')
        
        securl = FLIGHT_SPOTLIGHT_URL + '/set_air_traffic'

        headers = {"Authorization": "Bearer " + credentials['access_token']}
        for message in distinct_messages:
            
            unix_time = int(message['timestamp'].timestamp())
            # TODO Convert to a SingleAirtrafficObservation object
            payload = {"icao_address" : message['address'],"traffic_source" :message['msg_data']['traffic_source'], "source_type" : message['msg_data']['source_type'], "lat_dd" : message['msg_data']['lat_dd'], "lon_dd" : message['msg_data']['lon_dd'], "time_stamp" : unix_time,"altitude_mm" : message['msg_data']['altitude_mm'], "metadata": message['msg_data']['metadata']}
            
            response = requests.post(securl, data= payload, headers=headers)
            
            logging.info(response.status_code)

@app.task(name='start_openskies_stream')
def start_openskies_stream(view_port:str):   
    view_port = json.loads(view_port)
    
    # submit task to write to the flight stream
    lng_min = min(view_port[0], view_port[2])
    lng_max = max(view_port[0], view_port[2])
    lat_min = min(view_port[1], view_port[3])
    lat_max = max(view_port[1], view_port[3])

    heartbeat = env.get('HEARTBEAT_RATE_SECS', 2)
    heartbeat = int(heartbeat)
    my_credentials = flight_stream_helper.PassportCredentialsGetter()
    credentials = my_credentials.get_cached_credentials()
    FLIGHT_SPOTLIGHT_URL = os.getenv('FLIGHT_SPOTLIGHT_URL', 'http://localhost:5000')
    securl = FLIGHT_SPOTLIGHT_URL + '/set_air_traffic'
    headers = {"Authorization": "Bearer " + credentials['access_token']}
    now = arrow.now()
    one_minute_from_now = now.shift(seconds = 45)

    logger.info("Querying OpenSkies Network for one minute.. ")

    while arrow.now() < one_minute_from_now:
        url_data='https://opensky-network.org/api/states/all?'+'lamin='+str(lat_min)+'&lomin='+str(lng_min)+'&lamax='+str(lat_max)+'&lomax='+str(lng_max)
        openskies_username = env.get('OPENSKY_NETWORK_USERNAME')
        openskies_password = env.get('OPENSKY_NETWORK_PASSWORD')
        response= requests.get(url_data, auth=(openskies_username, openskies_password))
        logger.info(url_data)
        #LOAD TO PANDAS DATAFRAME
        col_name=['icao24','callsign','origin_country','time_position','last_contact','long','lat','baro_altitude','on_ground','velocity',       
        'true_track','vertical_rate','sensors','geo_altitude','squawk','spi','position_source']
        
        response_data = response.json()
        logger.debug(response_data)
        
        if response.status_code == 200:
            
            if response_data['states'] is not None:
                flight_df=pd.DataFrame(response_data['states'],columns=col_name)
                flight_df=flight_df.fillna('No Data') 
                
                all_observations = []
                for index, row in flight_df.iterrows():
                    metadata = {'velocity':row['velocity']}
                    
                    all_observations.append({"icao_address" : row['icao24'],"traffic_source" :2, "source_type" : 1, "lat_dd" : row['lat'], "lon_dd" : row['long'], "time_stamp" :  row['time_position'],"altitude_mm" :  row['baro_altitude'], 'metadata':metadata})    

                payload = {"observations":all_observations}    

                try:
                    response = requests.post(securl, json = payload, headers = headers)        
                except Exception as e:
                    logger.error("Error in posting Openskies Network data to Flight Spotlight")
                    logger.error(e)
                else:
                    response.json()                
        time.sleep(heartbeat)