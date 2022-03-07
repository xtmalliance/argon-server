from rtree import index
from os import environ as env
import redis

class OperationalIntentsIndexFactory():
    def __init__(self, index_name:str):
        self.idx = index.Index(index_name)

    def add_box_to_index(self, op_int_id, view, start_time, end_time):
        self.idx.insert(id = op_int_id, bounds = (view[0], view[1], view[2], view[3]), start_time = start_time, end_time = end_time)

    def generate_operational_intents_index(self) -> None:
        """This method generates a rTree index of currently active operational indexes """
    
        r = redis.Redis(host=env.get('REDIS_HOST',"redis"), port =env.get('REDIS_PORT',6379))   
        all_op_ints = r.keys(pattern='opint-*')

        operational_intent = all_op_ints.split('-')[1]

        for operational_intent_id in all_op_ints:
            operational_intent_view = r.get(operational_intent)
            view = [float(i) for i in operational_intent_view.split(",")]
            self.add_box_to_index(op_int_id = operational_intent_id, view = view, box= view)

    def check_box_intersection(self, view_box):

        intersections = [n for n in self.idx.intersection((view_box[0], view_box[1], view_box[2], view_box[3]))]        
        self.idx.close()
        return intersections