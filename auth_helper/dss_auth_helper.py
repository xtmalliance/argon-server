import json
import redis
import logging
from datetime import datetime, timedelta
logger = logging.getLogger('django')
import json
import redis
import requests
from os import environ as env
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
 
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)


class AuthorityCredentialsGetter():
    ''' All calls to the DSS require credentials from a authority, usually the CAA since they can provide access to the system '''
    def __init__(self):
        pass
        
    def get_cached_credentials(self, audience):  
        r = redis.Redis(host=env.get('REDIS_HOST',"redis"), port =env.get('REDIS_PORT',6379))   
        
        now = datetime.now()
        cache_key = audience + '_auth_dss_token'
        token_details = r.get(cache_key)
        
        if token_details:    
            token_details = json.loads(token_details)
            created_at = token_details['created_at']
            set_date = datetime.strptime(created_at,"%Y-%m-%dT%H:%M:%S.%f")
            if now < (set_date - timedelta(minutes=58)):
                credentials = self.get_read_credentials(audience)
                r.set(cache_key, json.dumps({'credentials': credentials, 'created_at':now.isoformat()}))
            else: 
                credentials = token_details['credentials']
        else:   
            credentials = self.get_read_credentials(audience)            
            access_token = credentials.get('access_token')
            if access_token: # there is no error in the token
                r.set(cache_key, json.dumps({'credentials': credentials, 'created_at':now.isoformat()}))            
                r.expire(cache_key, timedelta(minutes=58))
                
        return credentials
            
        
    def get_read_credentials(self, audience):        
        issuer = audience if audience =='localhost' else None

        if audience == 'localhost':
            # Test instance of DSS
            payload = {"grant_type":"client_credentials","intended_audience":env.get('DSS_SELF_AUDIENCE'),"scope": 'dss.read.identification_service_areas', "issuer":issuer}       
            
        else: 
            payload = {"grant_type":"client_credentials","client_id": env.get('AUTH_DSS_CLIENT_ID'),"client_secret": env.get('AUTH_DSS_CLIENT_SECRET'),"audience":audience,"scope": 'dss.read.identification_service_areas'}    
      
        url = env.get('DSS_AUTH_URL') + env.get('DSS_AUTH_TOKEN_ENDPOINT')        
        
        token_data = requests.post(url, params = payload)
        t_data = token_data.json()     
        return t_data
