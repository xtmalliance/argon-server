from walrus import Database
import os

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())


class ConsumerGroupOps():

    # def __init__(self):
    #     init_cg = self.get_consumer_group(create=True)

    def create_cg(self):
        self.get_consumer_group(create=True)
        
    def get_consumer_group(self,create=False):
        db = Database(host=os.environ.get("REDIS_HOST"), port=os.environ.get("REDIS_PORT"))   
        stream_keys = ['all_observations']
        
        cg = db.time_series('cg-obs', stream_keys)
        if create:
            for stream in stream_keys:
                db.xadd(stream, {'data': ''})

        if create:
            cg.create()
            cg.set_id('$')

        return cg.all_observations
