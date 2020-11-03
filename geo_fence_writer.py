# API to submit Geo fence into Spotlight -> for a non API call look at set_geo_fence_secured.py file in importers directory

from functools import wraps
import json
from __main__ import app
from flask_uuid import FlaskUUID
from os import environ as env
from six.moves.urllib.request import urlopen
from auth import AuthError, requires_auth, requires_scope
from flask import request, Response
import redis, celery
import geojson, requests
from geojson import Polygon
from datetime import datetime, timedelta


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

            headers = {"Authorization": "Bearer "+ self.credentials['access_token']}

            upper_limit = fence_feature['properties']['upper_limit']
            lower_limit = fence_feature['properties']['lower_limit']

            try:
                p = Polygon(fence_feature['geometry']['coordinates'])
                assert p.is_valid
                
            except AssertionError as ae:
                print("Invalid polygon in Geofence")
            else:
                payload = {"geo_fence" :geojson.dumps(p, sort_keys=True), "properties":json.dumps({"upper_limit":upper_limit, "lower_limit":lower_limit})}                
                securl = env.get("FLIGHT_SPOTLIGHT_URL")+ '/set_geo_fence'

                try:
                    response = requests.post(securl, data= payload, headers=headers)
                    print(response.content)                
                except Exception as e:
                    print(e)
                else:
                    print("Uploaded Geo Fence")                    

@celery.task()
def write_geo_fence(geo_fence): 
    my_credentials = PassportCredentialsGetter()
    credentials = my_credentials.get_write_credentials()

    my_uploader = GeoFenceUploader(credentials = credentials)
    my_uploader.upload_to_server(gf=geo_fence)



@requires_auth
@app.route("/submit_geo_fence", methods=['POST'])
def post_geo_fence():   

    try:
        assert request.headers['Content-Type'] == 'application/json'   
    except AssertionError as ae:     
        msg = {"message":"Unsupported Media Type"}
        return Response(json.dumps(msg), status=415, mimetype='application/json')
    else:    
        geo_fence = json.loads(request.data)

    task = write_geo_fence.delay(geo_fence)  # Send a job to the task queue

    op = json.dumps ({"message":"OK"})
    return Response(op, status=200, mimetype='application/json')
