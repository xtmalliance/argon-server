from walrus import Database
import os

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

REDIS_HOST = os.getenv('REDIS_HOST',"redis")
REDIS_PORT = 6379


class ConsumerGroupOps():

    # def __init__(self):
    #     init_cg = self.get_consumer_group(create=True)

    def create_cg(self):
        self.get_consumer_group(create=True)
        
    def get_consumer_group(self,create=False):
        db = Database(host=REDIS_HOST, port =REDIS_PORT)   
        stream_keys = ['all_observations']
        
        cg = db.time_series('cg-obs', stream_keys)
        if create:
            for stream in stream_keys:
                db.xadd(stream, {'data': ''})

        if create:
            cg.create()
            cg.set_id('$')

        return cg.all_observations
