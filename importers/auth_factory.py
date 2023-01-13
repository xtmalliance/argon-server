import os
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 

import json, time, requests
from datetime import datetime, timedelta
from typing import List
from dotenv import load_dotenv, find_dotenv
from os import environ as env
from common import get_redis
from auth_helper.dummy_oauth_infrastructure.dummy_oauth import NoAuth

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)


class PassportSpotlightCredentialsGetter():
    def __init__(self):
        pass
    def get_cached_credentials(self,audience:str= None, scopes: List[str]= None):  
        r = get_redis()

        if not audience:
            return {'error':"An audience paramter must be provided"}
        try: 
            scopes_str = ' '.join(scopes)
        except Exception as e: 
            return {'error':"An list of scopes paramter must be provided"}

        now = datetime.now()
        
        token_details = r.get('spotlight_write_air_traffic_token')
        if token_details:    
            token_details = json.loads(token_details)
            created_at = token_details['created_at']
            set_date = datetime.strptime(created_at,"%Y-%m-%dT%H:%M:%S.%f")
            if now < (set_date - timedelta(minutes=58)):
                credentials = self.get_write_credentials()
                r.set('spotlight_write_air_traffic_token', json.dumps({'credentials': credentials, 'created_at':now.isoformat()}))
            else: 
                credentials = token_details['credentials']
        else:   
            
            credentials = self.get_write_credentials()
            r.set('spotlight_write_air_traffic_token', json.dumps({'credentials': credentials, 'created_at':now.isoformat()}))
            r.expire("spotlight_write_air_traffic_token", timedelta(minutes=58))
            
        return credentials
            
        
    def get_write_credentials(self, audience:str, scopes:List[str]):        
        payload = {"grant_type":"client_credentials","client_id": env.get('SPOTLIGHT_WRITE_CLIENT_ID'),"client_secret": env.get('SPOTLIGHT_WRITE_CLIENT_SECRET'),"audience": audience,"scope": scopes}        
        url = env.get('PASSPORT_URL') + env.get('PASSPORT_TOKEN_URL')
        
        token_data = requests.post(url, data = payload)
        t_data = token_data.json()
        
        return t_data
    
     

class PassportCredentialsGetter():
    def __init__(self):
        pass

    def get_cached_credentials(self,audience:str= None, scopes: List[str]= None):  
        r = get_redis()

        if not audience:
            return {'error':"An audience paramter must be provided"}
        try: 
            scopes_str = ' '.join(scopes)
        except Exception as e: 
            return {'error':"An list of scopes paramter must be provided"}

        scopes_str = ' '.join(scopes)
        
        now = datetime.now()        
        
        token_details = r.get('blender_write_air_traffic_token')
        if token_details:    
            token_details = json.loads(token_details)
            created_at = token_details['created_at']
            set_date = datetime.strptime(created_at,"%Y-%m-%dT%H:%M:%S.%f")
            if now < (set_date - timedelta(minutes=58)):
                credentials = self.get_write_credentials(audience = audience, scopes = scopes_str)
                r.set('blender_write_air_traffic_token', json.dumps({'credentials': credentials, 'created_at':now.isoformat()}))
            else: 
                credentials = token_details['credentials']
        else:               
            credentials = self.get_write_credentials(audience = audience, scopes = scopes_str)
            if 'error' in credentials.keys():
                pass
            else:
                r.set('blender_write_air_traffic_token', json.dumps({'credentials': credentials, 'created_at':now.isoformat()}))
                r.expire("blender_write_air_traffic_token", timedelta(minutes=58))
            
        return credentials
            
        
    def get_write_credentials(self, audience:str, scopes:List[str]):        
        payload = {"grant_type":"client_credentials","client_id": env.get('BLENDER_WRITE_CLIENT_ID'),"client_secret": env.get('BLENDER_WRITE_CLIENT_SECRET'),"audience": audience,"scope": scopes}        
        url = env.get('PASSPORT_URL') + env.get('PASSPORT_TOKEN_URL')
       
        token_data = requests.post(url, data = payload)
        t_data = token_data.json()
        
        
        return t_data


class NoAuthCredentialsGetter():
    def __init__(self):
        pass

    def get_cached_credentials(self, audience:str, scopes: List[str]):       
        if not audience:
            return {'error':"An audience paramter must be provided"}
        try: 
            scopes_str = ' '.join(scopes)
        except Exception as e: 
            return {'error':"An list of scopes paramter must be provided"}

        audience = audience
        scopes = scopes_str
        adapter = NoAuth()
        token = adapter.issue_token(audience, scopes.split(' '))
            
        t_data = {'access_token': token}
        
        
        return t_data

