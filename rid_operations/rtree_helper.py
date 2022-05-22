from rtree import index
from typing import List
from os import environ as env
import redis
import json 
from shapely.geometry import Polygon
from rtree import index
from scd_operations.scd_data_definitions import OpInttoCheckDetails



class OperationalIntentsIndexFactory():
    def __init__(self, index_name:str):
        self.idx = index.Index(index_name)
        self.r = redis.Redis(host=env.get('REDIS_HOST',"redis"), port =env.get('REDIS_PORT',6379)) 

    def add_box_to_index(self,enumerated_id:int,  flight_id:str, view:List[float], start_time:str, end_time:str):        
        metadata = {"start_time":start_time, "end_time":end_time, "flight_id":flight_id }
        self.idx.insert(id = enumerated_id, coordinates= (view[0], view[1], view[2], view[3]),obj = metadata)

    def delete_from_index(self,enumerated_id:int, view:List[float]):                
        self.idx.delete(id = enumerated_id, coordinates= (view[0], view[1], view[2], view[3]))

    def generate_operational_intents_index(self) -> None:
        """This method generates a rTree index of currently active operational indexes """      
        
        all_op_ints = self.r.keys(pattern='flight_opint.*')
        for flight_idx, flight_id in enumerate(all_op_ints):                        
            flight_id_str = flight_id.decode().split('.')[1]        
            operational_intent_view_raw = self.r.get(flight_id)   
            operational_intent_view = json.loads(operational_intent_view_raw)            
            split_view = operational_intent_view['bounds'].split(",")
            start_time = operational_intent_view['start_time']
            end_time  = operational_intent_view['end_time']            
            view = [float(i) for i in split_view]            
            self.add_box_to_index(enumerated_id= flight_idx, flight_id = flight_id_str, view = view, start_time=start_time, end_time= end_time)

    def clear_rtree_index(self):
        """Method to delete all boxes from the index"""

        all_op_ints = self.r.keys(pattern='flight_opint.*')
        for flight_idx, flight_id in enumerate(all_op_ints):           
            operational_intent_view_raw = self.r.get(flight_id)   
            operational_intent_view = json.loads(operational_intent_view_raw)            
            split_view = operational_intent_view['bounds'].split(",")
            view = [float(i) for i in split_view]            
            self.delete_from_index(enumerated_id= flight_idx,view = view)

    def check_box_intersection(self, view_box:List[float]):
        intersections = [n.object for n in self.idx.intersection((view_box[0], view_box[1], view_box[2], view_box[3]), objects=True)]        
        return intersections

def check_polygon_intersection(op_int_details:List[OpInttoCheckDetails], polygon_to_check:Polygon ) -> True:     
    idx = index.Index()
    for pos, op_int_detail in enumerate(op_int_details):
        idx.insert(pos, op_int_detail.shape.bounds)


    op_ints_of_interest_ids = list(idx.intersection(polygon_to_check.bounds))

    does_intersect = []
    if op_ints_of_interest_ids: 
        for op_ints_of_interest_id in op_ints_of_interest_ids:
            existing_op_int = op_int_details[op_ints_of_interest_id]
            intersects = polygon_to_check.intersects(existing_op_int.shape)
            if intersects:
                does_intersect.append(True)
            else: 
                does_intersect.append(False)

        return all(does_intersect)


    else: 
        return False