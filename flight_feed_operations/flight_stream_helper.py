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
        self.obs_database = ['all_observations']               
        self.db = Database(host=url.hostname, port=url.port, username=url.username, password=url.password)   
        
    def create_push_stream(self):
        self.get_push_stream(create=True)
        
    def get_push_stream(self,create=False):
        # Create a time-series consumer group named "demo-ts" for the stream all_observation
        time_series = self.db.time_series('cg-type-push', self.obs_database)
        if create:
            for stream in self.stream_keys:
                self.db.xadd(stream, {'data': ''})                
            time_series.create()
            time_series.set_id('$')

        return time_series.all_observations
    
        
    def create_pull_stream(self):
        self.get_pull_stream(create=True)
        
    def get_pull_stream(self,create=False):
        # Create a time-series consumer group named "demo-ts" for the stream all_observation
        time_series = self.db.time_series('cg-type-pull', self.obs_database)
        if create:
            for stream in self.stream_keys:
                self.db.xadd(stream, {'data': ''})
            time_series.create()
            time_series.set_id('$')

        return time_series.all_observations
    
    
    
    
class ObservationReadOperations():
    
    def get_observations(self, all_observations):
        
        messages = all_observations.read()
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
        token_details = r.get('access_token_details')
        if token_details:    
            token_details = json.loads(token_details)
            created_at = token_details['created_at']
            set_date = datetime.strptime(created_at,"%Y-%m-%dT%H:%M:%S.%f")
            if now < (set_date - timedelta(minutes=58)):
                credentials = self.get_write_credentials()
                r.set('access_token_details', json.dumps({'credentials': credentials, 'created_at':now.isoformat()}))
            else: 
                credentials = token_details['credentials']
        else:   
            
            credentials = self.get_write_credentials()
            r.set('access_token_details', json.dumps({'credentials': credentials, 'created_at':now.isoformat()}))
            
        return credentials
            
            
    def get_write_credentials(self):        
        payload = {"grant_type":"client_credentials","client_id": os.getenv('SPOTLIGHT_WRITE_CLIENT_ID'),"client_secret": os.getenv('SPOTLIGHT_WRITE_CLIENT_SECRET'),"audience": os.getenv('SPOTLIGHT_AUDIENCE'),"scope": os.getenv('SPOTLIGHT_AIR_TRAFFIC_SCOPE')}        
        url = os.getenv('PASSPORT_URL') + os.getenv('PASSPORT_TOKEN_URL')
        
        token_data = requests.post(url, data = payload)
        t_data = token_data.json()
        
        return t_data

