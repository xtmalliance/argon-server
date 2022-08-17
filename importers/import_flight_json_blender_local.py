## A file to import flight data into the Tile 38 instance. 
import json, time, requests
from datetime import datetime, timedelta
from os.path import dirname, abspath
from dotenv import load_dotenv, find_dotenv
from os import environ as env
from common import get_redis
import os
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

class PassportCredentialsGetter():
    def __init__(self):
        pass

    def get_cached_credentials(self):  
        r = get_redis()
        
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
            if 'error' in credentials.keys():
                pass
            else:
                r.set('blender_write_air_traffic_token', json.dumps({'credentials': credentials, 'created_at':now.isoformat()}))
                r.expire("blender_write_air_traffic_token", timedelta(minutes=58))
            
        return credentials
            
        
    def get_write_credentials(self):        
        payload = {"grant_type":"client_credentials","client_id": env.get('BLENDER_WRITE_CLIENT_ID'),"client_secret": env.get('BLENDER_WRITE_CLIENT_SECRET'),"audience": env.get('BLENDER_AUDIENCE'),"scope": env.get('BLENDER_WRITE_SCOPE')}        
        url = env.get('PASSPORT_URL') +env.get('PASSPORT_TOKEN_URL')
       
        token_data = requests.post(url, data = payload)
        t_data = token_data.json()
        
        
        return t_data

class BlenderUploader():
    
    def __init__(self, credentials):        
        
        self.timestamps = [1590000000000,1590000005000,1590000010000,1590000015000,1590000020000]    
        self.credentials = credentials
    
    def upload_to_server(self, filename):
        with open(filename, "r") as traffic_json_file:
            traffic_json = traffic_json_file.read()
            
        traffic_json = json.loads(traffic_json)
        
       
        for timestamp in self.timestamps: 
            
            current_timestamp_readings =  [x for x in traffic_json if x['timestamp'] == timestamp]
            
            for current_reading in current_timestamp_readings:
                icao_address = current_reading['icao_address']
                traffic_source = current_reading["traffic_source"]
                source_type = current_reading["source_type"]
                lat_dd = current_reading['lat_dd']
                lon_dd = current_reading['lon_dd']
                time_stamp = current_reading['timestamp']
                altitude_mm = current_reading['altitude_mm']                
                metadata = current_reading['metadata']

                # print(timestamp)
                headers = {"Content-Type":'application/json',"Authorization": "Bearer "+ self.credentials['access_token']}
                
                payload = {"observations":[{"icao_address" : icao_address,"traffic_source" :traffic_source, "source_type" : source_type, "lat_dd" : lat_dd, "lon_dd" : lon_dd, "time_stamp" : time_stamp,"altitude_mm" : altitude_mm, 'metadata':metadata}]}
                
                securl = 'http://localhost:8000/flight_stream/set_air_traffic' # set this to self (Post the json to itself)
                try:
                    response = requests.post(securl, json = payload, headers = headers)
                    
                except Exception as e:
                    print(e)
                else:                    
                    print("Sleeping 10 seconds..")
                    time.sleep(10)


if __name__ == '__main__':
    

    my_credentials = PassportCredentialsGetter()
    credentials = my_credentials.get_cached_credentials()
    parent_dir = dirname(abspath(__file__))  #<-- absolute dir the raw input file  is in
    rel_path = "air_traffic_samples/micro_flight_data_single.json"
    abs_file_path = os.path.join(parent_dir, rel_path)
    my_uploader = BlenderUploader(credentials=credentials)
    my_uploader.upload_to_server(filename=abs_file_path)