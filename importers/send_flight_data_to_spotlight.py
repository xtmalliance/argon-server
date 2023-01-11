## A file to import flight data into the Secured Flight Spotlight instance. 

import time
from django.views.generic import base
import requests 
from dotenv import load_dotenv, find_dotenv
import json
from auth_factory import NoAuthCredentialsGetter, PassportSpotlightCredentialsGetter
from os import environ as env
import redis
from common import get_redis
from datetime import datetime, timedelta
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

class FlightSpotlightUploader():
    
    def __init__(self, credentials):
        
        self.timestamps = [1590000000000,1590000005000, 1590000010000,1590000015000, 1590000020000]         
        self.credentials = credentials
    
    def upload_to_server(self, filename):
        with open(filename, "r") as traffic_json_file:
            traffic_json = traffic_json_file.read()
            
        traffic_json = json.loads(traffic_json)['observations']        
       
        for timestamp in self.timestamps: 
            
            current_timestamp_readings =  [x for x in traffic_json if x['timestamp'] == timestamp]
            
            for current_reading in current_timestamp_readings:
                icao_address = current_reading['icao_address']
                traffic_source = current_reading["traffic_source"]
                source_type = int(current_reading["source_type"])
                lat_dd = current_reading['lat_dd']
                lon_dd = current_reading['lon_dd']
                time_stamp = current_reading['timestamp']
                altitude_mm = current_reading['altitude_mm']
                metadata = current_reading['metadata']

                headers = {"Authorization": "Bearer "+ self.credentials['access_token']}
                payload = {"icao_address" : icao_address,"traffic_source" :traffic_source, "source_type" : source_type, "lat_dd" : lat_dd, "lon_dd" : lon_dd, "time_stamp" : time_stamp,"altitude_mm" : altitude_mm, 'metadata':metadata}
                baseurl = env.get('FLIGHT_SPOTLIGHT_URL','http://localhost:5000')
                securl = baseurl + '/set_air_traffic'
                try:
                    
                    response = requests.post(securl, json = payload, headers = headers)
                    
                    
                except Exception as e:
                    print(e)
                else:
                    print("Sleeping 5 seconds..")
                    time.sleep(5)
                
           

if __name__ == '__main__':

    # my_credentials = PassportSpotlightCredentialsGetter()
    my_credentials = NoAuthCredentialsGetter()    
    credentials = my_credentials.get_cached_credentials(audience='testflight.flightspotlight.com', scopes=['spotlight.write'])
    
    my_uploader = FlightSpotlightUploader(credentials = credentials)
    my_uploader.upload_to_server(filename='air_traffic_samples/micro_flight_data.json')