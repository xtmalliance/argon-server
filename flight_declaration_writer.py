# API to submit Flight Declarations into Spotlight

from functools import wraps
import json
from __main__ import app
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
        
        token_details = r.get('flight_declaration_access_token_details')
        if token_details:    
            token_details = json.loads(token_details)
            created_at = token_details['created_at']
            set_date = datetime.strptime(created_at,"%Y-%m-%dT%H:%M:%S.%f")
            if now < (set_date - timedelta(minutes=58)):
                credentials = self.get_write_credentials()
                r.set('flight_declaration_access_token_details', json.dumps({'credentials': credentials, 'created_at':now.isoformat()}))
            else: 
                credentials = token_details['credentials']
        else:   
            
            credentials = self.get_write_credentials()
            r.set('flight_declaration_access_token_details', json.dumps({'credentials': credentials, 'created_at':now.isoformat()}))
            
            r.expire("flight_declaration_access_token_details", timedelta(minutes=58))
            
        return credentials
            
        
    def get_write_credentials(self):        
        payload = {"grant_type":"client_credentials","client_id": env.get('PASSPORT_WRITE_CLIENT_ID'),"client_secret": env.get('PASSPORT_WRITE_CLIENT_SECRET'),"audience": env.get('PASSPORT_WRITE_AUDIENCE'),"scope": env.get('PASSPORT_FLIGHT_DECLARATION_SCOPE')}        
        url = env.get('PASSPORT_URL') + env.get('PASSPORT_TOKEN_URL')        
        token_data = requests.post(url, data = payload)
        t_data = token_data.json()        
        return t_data

class FlightDeclarationsUploader():
    
    def __init__(self, credentials):
    
        self.credentials = credentials
    
    def upload_to_server(self, flight_declaration_json):
        
        flight_declaration_data = json.loads(flight_declaration_json)
        # print (flight_declaration_data['flight_declaration']['parts'])

        headers = {"Authorization": "Bearer "+ self.credentials['access_token']}
        
        payload = {"flight_declaration" : json.dumps(flight_declaration_data)}                

        securl = env.get('FLIGHT_SPOTLIGHT_URL') + '/set_flight_declaration'
        try:
            response = requests.post(securl, data= payload, headers=headers)
            print(response.content)                
        except Exception as e:
            print(e)
        else:
            print("Uploaded Flight Declarations")                    

@celery.task()
def write_flight_declaration(fd): 
    my_credentials = PassportCredentialsGetter()
    credentials = my_credentials.get_write_credentials()

    my_uploader = FlightDeclarationsUploader(credentials = credentials)
    my_uploader.upload_to_server(flight_declaration_json=fd)



@requires_auth
@app.route("/submit_flight_declaration/", methods=['POST'])
def post_flight_declaration():
    

    try:
        assert request.headers['Content-Type'] == 'application/json'   
    except AssertionError as ae:     
        msg = {"message":"Unsupported Media Type"}
        return Response(json.dumps(msg), status=415, mimetype='application/json')
    else:    
        req = json.loads(request.data)

    try:
        flight_declaration_data = req("flight_declaration")

    except KeyError as ke:
        msg = json.dumps({"message":"One parameter are required: observations with a list of observation objects. One or more of these were not found in your JSON request. For sample data see: https://github.com/openskies-sh/airtraffic-data-protocol-development/blob/master/Airtraffic-Data-Protocol.md#sample-traffic-object"})
        
        return Response(msg, status=400, mimetype='application/json')

    else:
        task = write_flight_declaration.delay(flight_declaration_data)  # Send a job to the task queuervation)  # Send a job to the task queue


    op = json.dumps ({"message":"OK"})
    return Response(op, status=200, mimetype='application/json')
