import os, json
import logging
from .data_definitions import SingleAirtrafficObservation
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
    logging.debug("Writing observation..")
    
    my_stream_ops = flight_stream_helper.StreamHelperOps()   
    cg = my_stream_ops.get_pull_cg()     
    msg_id = cg.all_observations.add(obs)      
    cg.all_observations.trim(1000)
    return msg_id

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
    now = arrow.now()
    two_minutes_from_now = now.shift(seconds = 120)

    logger.info("Querying OpenSkies Network for one minute.. ")

    my_stream_ops = flight_stream_helper.StreamHelperOps()   
    cg = my_stream_ops.get_pull_cg() 
    while arrow.now() < two_minutes_from_now:
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
                    
                    obs = {"icao_address" : row['icao24'],"traffic_source" :2, "source_type" : 1, "lat_dd" : row['lat'], "lon_dd" : row['long'], "time_stamp" :  row['time_position'],"altitude_mm" :  row['baro_altitude'], 'metadata':metadata}
                        
                    msg_id = cg.all_observations.add(obs)      
                    cg.all_observations.trim(1000)   
    
        time.sleep(heartbeat)