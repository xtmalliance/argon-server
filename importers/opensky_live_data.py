import os
from os import environ as env
from datetime import datetime, timedelta
from dotenv import load_dotenv, find_dotenv
import json
import requests
from common import get_redis()
import pandas as pd
import logging


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
            r.set('blender_write_air_traffic_token', json.dumps({'credentials': credentials, 'created_at':now.isoformat()}))
            r.expire("blender_write_air_traffic_token", timedelta(minutes=58))
            
        return credentials
            
    def get_write_credentials(self):        
        payload = {"grant_type":"client_credentials","client_id": env.get('BLENDER_WRITE_CLIENT_ID'),"client_secret": env.get('BLENDER_WRITE_CLIENT_SECRET'),"audience": env.get('BLENDER_AUDIENCE'),"scope": env.get('BLENDER_WRITE_SCOPE')}        
        url = env.get('PASSPORT_URL') + env.get('PASSPORT_TOKEN_URL')
        
        token_data = requests.post(url, data = payload)
        t_data = token_data.json()
        
        return t_data

if __name__ == '__main__':

    my_credentials = PassportCredentialsGetter()
    credentials = my_credentials.get_cached_credentials()
    
    
    username = os.environ.get('OPENSKY_NETWORK_USERNAME')
    password = os.environ.get('OPENSKY_NETWORK_PASSWORD')

    # bbox = (min latitude, max latitude, min longitude, max longitude)

    view_port=(45.8389, 47.8229, 5.9962, 10.5226)
    lat_min = min(view_port[0], view_port[2])
    lat_max = max(view_port[0], view_port[2])
    lng_min = min(view_port[1], view_port[3])
    lng_max = max(view_port[1], view_port[3])

    url_data='https://opensky-network.org/api/states/all?'+'lamin='+str(lat_min)+'&lomin='+str(lng_min)+'&lamax='+str(lat_max)+'&lomax='+str(lng_max)

    response=requests.get(url_data, auth=(username, password)).json()

    #LOAD TO PANDAS DATAFRAME
    col_name=['icao24','callsign','origin_country','time_position','last_contact','long','lat','baro_altitude','on_ground','velocity',       
    'true_track','vertical_rate','sensors','geo_altitude','squawk','spi','position_source']
    flight_df=pd.DataFrame(response['states'],columns=col_name)
    flight_df=flight_df.fillna('No Data') 
    
    all_observations = []
    for index, row in flight_df.iterrows():
        metadata = {'velocity':row['velocity']}
        
        all_observations.append({"icao_address" : row['icao24'],"traffic_source" :2, "source_type" : 1, "lat_dd" : row['lat'], "lon_dd" : row['long'], "time_stamp" :  row['time_position'],"altitude_mm" :  row['baro_altitude'], 'metadata':metadata})    

    headers = {"Content-Type":'application/json',"Authorization": "Bearer "+ credentials['access_token']}
    
    payload = {"observations":all_observations}    
    securl = 'http://localhost:8000/set_air_traffic' # set this to self (Post the json to itself)

    try:
        response = requests.post(securl, json = payload, headers = headers)        
    except Exception as e:
        logging.error("Error in posting data to Spotlight")
        logging.error(e.json())
    else:
        response.json()