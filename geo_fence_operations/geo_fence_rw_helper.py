# API to submit Geo fence into Spotlight -> for a non API call look at set_geo_fence_secured.py file in importers directory

from functools import wraps
import json
import os
from os import environ as env

import redis, celery
import geojson, requests
from geojson import Polygon
from datetime import datetime, timedelta
import logging


class PassportCredentialsGetter():
    def __init__(self):
        pass

    def get_cached_credentials(self):  
        r = redis.Redis()
        
        now = datetime.now()
        
        token_details = r.get('geofence_token_details')
        if token_details:    
            token_details = json.loads(token_details)
            created_at = token_details['created_at']
            set_date = datetime.strptime(created_at,"%Y-%m-%dT%H:%M:%S.%f")
            if now < (set_date - timedelta(minutes=58)):
                credentials = self.get_write_credentials()
                r.set('geofence_token_details', json.dumps({'credentials': credentials, 'created_at':now.isoformat()}))
            else: 
                credentials = token_details['credentials']
        else:               
            credentials = self.get_write_credentials()
            error = credentials.get('error')
            if not error: # there is no error in the token
                r.set('geofence_token_details', json.dumps({'credentials': credentials, 'created_at':now.isoformat()}))            
                r.expire("geofence_token_details", timedelta(minutes=58))
            
        return credentials
            
        
    def get_write_credentials(self):        
        payload = {"grant_type":"client_credentials","client_id": env.get('PASSPORT_WRITE_CLIENT_ID'),"client_secret": env.get('PASSPORT_WRITE_CLIENT_SECRET'),"audience": env.get('PASSPORT_WRITE_AUDIENCE'),"scope": env.get('PASSPORT_GEO_FENCE_SCOPE')}            
        url = env.get('PASSPORT_URL') +env.get('PASSPORT_TOKEN_URL')        
        token_data = requests.post(url, data = payload)
        t_data = token_data.json()
        
        return t_data




class GeoFenceUploader():
    
    def __init__(self, credentials):
        
        self.credentials = credentials
    
    def upload_to_server(self, gf):
        geo_fence_data = json.loads(gf)
        for fence_feature in geo_fence_data['features']:
            headers = {"Authorization": "Bearer " + self.credentials['access_token']}
            upper_limit = fence_feature['properties']['upper_limit']
            lower_limit = fence_feature['properties']['lower_limit']
            try:
                p = Polygon(fence_feature['geometry']['coordinates'])
                assert p.is_valid
                
            except AssertionError as ae:
                print("Invalid polygon in Geofence")
                return {"message":"Invalid polygon in Geofence"}
            else:
                payload = {"geo_fence" :geojson.dumps(p, sort_keys=True), "properties":json.dumps({"upper_limit":upper_limit, "lower_limit":lower_limit})}
                securl = env.get("FLIGHT_SPOTLIGHT_URL", "")

                try:
                    assert securl != ""
                except AssertionError as ae: 
                    return {"message":"FLIGHT_SPOTLIGHT_URL not set in the environment"}
                else:
                    securl = env.get("FLIGHT_SPOTLIGHT_URL")+ '/set_geo_fence'
                    try:
                        response = requests.post(securl, data= payload, headers=headers)
                        logging.debug(response.content)                
                    except Exception as e:
                        logging.error(e)
                    else:            
                        logging.debug("Uploaded Geofence")
                        # print("Uploaded Geofence")                 
                        return {"message":"Successfully uploaded Geofence"}   
