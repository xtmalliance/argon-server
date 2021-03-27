from walrus import Database
import os
from urllib.parse import urlparse
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

url = urlparse(os.environ.get("REDIS_URL"))

class ConsumerGroupOps():

    # def __init__(self):
    #     init_cg = self.get_consumer_group(create=True)

    def create_cg(self):
        self.get_consumer_group(create=True)
        
    def get_consumer_group(self,create=False):
        # db = Database(host=os.environ.get("REDIS_HOST"), port=os.environ.get("REDIS_PORT"))  
        print(url)
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
