import os
from os import environ as env
from dotenv import load_dotenv, find_dotenv
import json
from os.path import dirname, abspath
import requests

import time
import arrow
from auth_factory import PassportCredentialsGetter, NoAuthCredentialsGetter

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

if __name__ == '__main__':

    # my_credentials = PassportCredentialsGetter()
    my_credentials = NoAuthCredentialsGetter()
    credentials = my_credentials.get_cached_credentials(audience='testflight.flightblender.com', scopes=['blender.write'])
    
    parent_dir = dirname(abspath(__file__))  #<-- absolute dir the raw input file  is in
    rel_path = "aircraft_states/flight_1_rid_aircraft_state.json"
    abs_file_path = os.path.join(parent_dir, rel_path)

    with open(abs_file_path, "r") as aircraft_state_file:
        state_json = aircraft_state_file.read()
        
    state_json = json.loads(state_json)
    aircraft_type = state_json['flight_details']['aircraft_type']

    metadata = {"aircraft_type": aircraft_type}

    flight_states = state_json['states']
    flight_id = state_json['flight_details']['rid_details']["id"]

    headers = {"Content-Type":'application/json',"Authorization": "Bearer "+ credentials['access_token']}
    securl = env.get("BLENDER_FQDN","http://localhost:8000/") +'/flight_stream/set_air_traffic'     
    
    for flight_state in flight_states:
        time_stamp = arrow.now().int_timestamp
        payload = {"observations":[{"icao_address" : flight_id,"traffic_source" :11, "source_type" : 1, "lat_dd" : flight_state['position']['lat'], "lon_dd" :  flight_state['position']['lng'], "time_stamp" : time_stamp,"altitude_mm" :  flight_state['position']['alt'], 'metadata':metadata}]}    
    
        try:
            response = requests.post(securl, json = payload, headers = headers)        
        except Exception as e:
            print(e)
        else:
            response.json()
        print("Submitted waiting 15 seconds..")
        time.sleep(3)

