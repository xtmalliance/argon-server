# API to submit Flight Declarations into Spotlight
# from flask import Blueprint, current_app
from functools import wraps
from os import environ as env
from six.moves.urllib.request import urlopen
from auth import AuthError, requires_auth, requires_scope
import redis, json
import geojson, requests
from flask import Flask, current_app
from geojson import Polygon
from datetime import datetime, timedelta


# fd_blueprint = Blueprint('flight_declaration_writer', __name__)
 
REDIS_HOST = os.getenv('REDIS_HOST',"redis")
REDIS_PORT = 6379


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
        token_response = requests.post(url, data = payload)
        if token_response.status_code == 200:
            t_data = token_response.json()        
        else:
            t_data = {}
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
            current_app.logging.debug(response.content)                
        except Exception as e:
            current_app.logging.error(e)
        else:            
            current_app.logging.debug("Uploaded Flight Declarations")                    
            return "Uploaded Flight Declarations"
