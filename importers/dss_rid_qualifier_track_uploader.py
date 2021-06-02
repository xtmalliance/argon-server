import os
from os import environ as env, stat
from datetime import datetime, timedelta
from dotenv import load_dotenv, find_dotenv
import json
from os.path import dirname, abspath
import requests
import redis
import time
import arrow

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

class PassportCredentialsGetter():
    def __init__(self):
        pass

    def get_cached_credentials(self):  
        r = redis.Redis(host=os.getenv('REDIS_HOST'), port =os.getenv('REDIS_PORT'))   
        
        now = datetime.now()
        
        token_details = r.get('blender_write_air_traffic_token')
        if token_details:    
            token_details = json.loads(token_details)
            created_at = token_details['created_at']
            set_date = datetime.strptime(created_at,"%Y-%m-%dT%H:%M:%S.%f")
            if now < (set_date - timedelta(minutes=58)):
                credentials = self.get_write_credentials()
                r.set('blender_write_air_traffic_token', json.dumps({'credentials': credentials, 'created_at':now.isoformat()}))
            else: 
                credentials = token_details['credentials']
        else:   
            
            credentials = self.get_write_credentials()
            r.set('blender_write_air_traffic_token', json.dumps({'credentials': credentials, 'created_at':now.isoformat()}))
            r.expire("blender_write_air_traffic_token", timedelta(minutes=58))
            
        return credentials
            
        
    def get_write_credentials(self):        
        payload = {"grant_type":"client_credentials","client_id": env.get('BLENDER_WRITE_CLIENT_ID'),"client_secret": env.get('BLENDER_WRITE_CLIENT_SECRET'),"audience": env.get('BLENDER_AUDIENCE'),"scope": env.get('BLENDER_WRITE_SCOPE')}        
        url = env.get('PASSPORT_URL') +env.get('PASSPORT_TOKEN_URL')
        
        token_data = requests.post(url, data = payload)
        t_data = token_data.json()
        
        
        return t_data

if __name__ == '__main__':

    my_credentials = PassportCredentialsGetter()
    credentials = my_credentials.get_cached_credentials()
    
    parent_dir = dirname(abspath(__file__))  #<-- absolute dir the raw input file  is in
    rel_path = "air_traffic_samples/flight_1_rid_aircraft_state.json"
    abs_file_path = os.path.join(parent_dir, rel_path)

    with open(abs_file_path, "r") as aircraft_state_file:
        state_json = aircraft_state_file.read()
        
    state_json = json.loads(state_json)
    aircraft_type = state_json['flight_telemetry']['aircraft_type']

    metadata = {"aircraft_type": aircraft_type}

    flight_states = state_json['flight_telemetry']['states']
    flight_id = state_json['flight_details']["serial_number"]

    headers = {"Content-Type":'application/json',"Authorization": "Bearer "+ credentials['access_token']}
    securl = env.get("BLENDER_FQDN","http://localhost:8000/") +'/set_air_traffic'     
    
    for flight_state in flight_states:
        time_stamp = arrow.now().int_timestamp
        payload = {"observations":[{"icao_address" : flight_id,"traffic_source" :11, "source_type" : 1, "lat_dd" : flight_state['position']['lat'], "lon_dd" :  flight_state['position']['lon'], "time_stamp" : time_stamp,"altitude_mm" :  flight_state['position']['alt'], 'metadata':metadata}]}    
    
        try:
            response = requests.post(securl, json = payload, headers = headers)        
        except Exception as e:
            print(e)
        else:
            response.json()
        time.sleep(1)

