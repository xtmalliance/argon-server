from walrus import Database
import os
from urllib.parse import urlparse
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

url = urlparse(os.environ.get("REDIS_URL"))

class ConsumerGroupOps():
    # def __init__(self):
        
        # self.stream_keys = ['all_observations','rid_qualifier']

    def create_rid_qualifier(self):
        self.get_rid_qualifier_group(create=True)

    def create_all_obs(self):
        self.get_all_observations_group(create=True)
        
    def get_all_observations_group(self,create=False):
        
        db = Database(host=url.hostname, port=url.port, username=url.username, password=url.password)   
        
        stream_keys = ['all_observations']
        cg = db.time_series('cg-obs', stream_keys)
        if create:
            for stream in stream_keys:
                db.xadd(stream, {'data': ''})

        if create:
            cg.create()
            cg.set_id('$')

        return cg.all_observations

    def get_rid_qualifier_group(self,create=False):
        
        db = Database(host=url.hostname, port=url.port, username=url.username, password=url.password)   
        stream_keys = ['rid_qualifier']
        
        cg = db.time_series('cg-ridq', stream_keys)
        if create:
            for stream in stream_keys:
                db.xadd(stream, {'data': ''})

        if create:
            cg.create()
            cg.set_id('$')

        return cg.rid_qualifier
