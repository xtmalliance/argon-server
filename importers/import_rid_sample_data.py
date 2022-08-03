import os
from os import environ as env
from datetime import datetime, timedelta
from dotenv import load_dotenv, find_dotenv
import json
from os.path import dirname, abspath
import arrow, time
import requests
from dataclasses import dataclass, asdict
import redis
from typing import Optional

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

@dataclass
class RIDOperatorDetails():
  id: str
  operator_id: Optional[str]
  operation_description: Optional[str]
  serial_number: Optional[str]
  registration_number: Optional[str]
  aircraft_type:str = 'Helicopter'

class PassportCredentialsGetter():
    def __init__(self):
        pass

    def get_cached_credentials(self):  
        r = redis.Redis(host=env.get('REDIS_HOST',"redis"), port =env.get('REDIS_PORT',6379))   
        
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
        
        url = env.get('PASSPORT_URL') + env.get('PASSPORT_TOKEN_URL')
        
        token_data = requests.post(url, data = payload)
        t_data = token_data.json()
        
        return t_data

class BlenderUploader():
    
    def __init__(self, credentials):        
    
        self.credentials = credentials
    
    def upload_to_server(self, filename):
        with open(filename, "r") as rid_json_file:
            rid_json = rid_json_file.read()
            
        rid_json = json.loads(rid_json)
        
        states = rid_json['current_states']
        rid_operator_details  = rid_json['flight_details']
        rid_operator_details = RIDOperatorDetails(
            id="382b3308-fa11-4629-a966-84bb96d3b4db",
            serial_number='d29dbf50-f411-4488-a6f1-cf2ae4d4237a',
            operation_description="Medicine Delivery",
            operator_id='CHE-076dh0dq  ',
            registration_number='CHE-5bisi9bpsiesw',
        )

        for state in states: 
            headers = {"Content-Type":'application/json',"Authorization": "Bearer "+ self.credentials['access_token']}            
            # payload = {"observations":[{"icao_address" : icao_address,"traffic_source" :traffic_source, "source_type" : source_type, "lat_dd" : lat_dd, "lon_dd" : lon_dd, "time_stamp" : time_stamp,"altitude_mm" : altitude_mm, 'metadata':metadata}]}            

            payload = {"observations":[{"current_states":[state], "flight_details": asdict(rid_operator_details) }]}
            
            securl = 'http://localhost:8000/rid/flight_data' # set this to self (Post the json to itself)
            try:
                response = requests.put(securl, json = payload, headers = headers)
                
            except Exception as e:                
                print(e)
            else:
                if response.status_code == 201:
                    print("Sleeping 3 seconds..")
                    time.sleep(3)
                else: 
                    print(response.json())


if __name__ == '__main__':
    

    my_credentials = PassportCredentialsGetter()
    credentials = my_credentials.get_cached_credentials()
    parent_dir = dirname(abspath(__file__))  #<-- absolute dir the raw input file  is in
    
    rel_path = "rid_samples/flight_1_rid_aircraft_state.json"
    abs_file_path = os.path.join(parent_dir, rel_path)
    my_uploader = BlenderUploader(credentials=credentials)
    my_uploader.upload_to_server(filename=abs_file_path)