from walrus import Database
from datetime import datetime, timedelta
import os
import json, redis
import logging
import requests
from urllib.parse import urlparse

from itertools import zip_longest
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

url = urlparse(os.environ.get("REDIS_URL"))

# iterate a list in batches of size n
def batcher(iterable, n):
    args = [iter(iterable)] * n
    return zip_longest(*args)


class StreamHelperOps():
    def __init__(self):
        self.stream_keys = ['all_observations']
        
        self.db = Database(host=url.hostname, port=url.port)   
        
    def create_push_cg(self):
        self.get_push_cg(create=True)


    def get_push_cg(self,create=False):
        
        
        cg = self.db.time_series('cg-push', self.stream_keys)
        if create:
            for stream in self.stream_keys:
                self.db.xadd(stream, {'data': ''})
            cg.create()
            cg.set_id('$')

        return cg

    def create_pull_cg(self):
        self.get_pull_cg(create=True)
        
    def get_pull_cg(self,create=False):              
        cg = self.db.time_series('cg-pull', self.stream_keys)

        if create:
            for stream in self.stream_keys:
                self.db.xadd(stream, {'data': ''})

            cg.create()
            cg.set_id('$')

        return cg
    
class ObservationReadOperations():
    
    def get_observations(self, push_cg):
        
        messages = push_cg.read()
        pending_messages = []
        
        my_credentials = PassportCredentialsGetter()
        credentials = my_credentials.get_cached_credentials()
        if 'error' in credentials: 
            logging.error('Error in getting credentials %s' % credentials)
        else:
            for message in messages:             
                pending_messages.append({'timestamp': message.timestamp,'seq': message.sequence, 'msg_data':message.data, 'address':message.data['icao_address'], 'metadata':message['metadata']})
        return pending_messages
        
        
class PassportCredentialsGetter():
    def __init__(self):
        pass

    def get_cached_credentials(self):  
        r = redis.Redis(host=os.getenv('REDIS_HOST',"redis"), port =os.getenv('REDIS_PORT',6379))   
        now = datetime.now()
        cache_key = 'airtraffic_access_token_details'
        token_details = r.get(cache_key)
        if token_details:    
            token_details = json.loads(token_details)
            created_at = token_details['created_at']
            set_date = datetime.strptime(created_at,"%Y-%m-%dT%H:%M:%S.%f")
            if now < (set_date - timedelta(minutes=58)):
                credentials = self.get_write_credentials()
                r.set(cache_key, json.dumps({'credentials': credentials, 'created_at':now.isoformat()}))
            else: 
                credentials = token_details['credentials']
        else:   
            
            credentials = self.get_write_credentials()
            r.set(cache_key, json.dumps({'credentials': credentials, 'created_at':now.isoformat()}))
            r.expire(cache_key, timedelta(minutes=58))
        return credentials
            
            
    def get_write_credentials(self):        
        payload = {"grant_type":"client_credentials","client_id": os.getenv('SPOTLIGHT_WRITE_CLIENT_ID'),"client_secret": os.getenv('SPOTLIGHT_WRITE_CLIENT_SECRET'),"audience": os.getenv('SPOTLIGHT_AUDIENCE'),"scope": os.getenv('SPOTLIGHT_AIR_TRAFFIC_SCOPE')}        
        url = os.getenv('PASSPORT_URL') + os.getenv('PASSPORT_TOKEN_URL')
        
        token_data = requests.post(url, data = payload)
        t_data = token_data.json()
        
        return t_data

