from rtree import index
from os import environ as env
import redis
import json 

class OperationalIntentsIndexFactory():
    def __init__(self, index_name:str):
        self.idx = index.Index(index_name)

    def add_box_to_index(self,enumerated_id:int,  op_int_id, view:str, start_time:str, end_time:str):
        
        metadata = {"start_time":start_time, "end_time":end_time, "op_int_id":op_int_id }
        self.idx.insert(id = enumerated_id, coordinates= (view[0], view[1], view[2], view[3]),obj = metadata)

    def generate_operational_intents_index(self) -> None:
        """This method generates a rTree index of currently active operational indexes """
    
        r = redis.Redis(host=env.get('REDIS_HOST',"redis"), port =env.get('REDIS_PORT',6379))   
        all_op_ints = r.keys(pattern='opint.*')
        
        for op_int_idx, operational_intent_id in enumerate(all_op_ints):
            
            operational_intent_str = str(operational_intent_id).split('.')[1]            
            operational_intent_view_raw = r.get(operational_intent_id)   
            operational_intent_view = json.loads(operational_intent_view_raw)
            
            split_view = operational_intent_view['bounds'].split(",")
            start_time = operational_intent_view['start_time']
            end_time  = operational_intent_view['end_time']

            
            view = [float(i) for i in split_view]
            
            self.add_box_to_index(enumerated_id= op_int_idx, op_int_id = operational_intent_str, view = view, start_time=start_time, end_time= end_time)

    def check_box_intersection(self, view_box, ):

        intersections = [n.object for n in self.idx.intersection((view_box[0], view_box[1], view_box[2], view_box[3]), objects=True)]        
        self.idx.close()
        print(intersections)
        return intersections