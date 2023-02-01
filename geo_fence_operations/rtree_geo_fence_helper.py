from rtree import index
import arrow
from auth_helper.common import get_redis
import hashlib
from typing import Union, List
from django.db.models import QuerySet
from .models import GeoFence

class GeoFenceRTreeIndexFactory():
    def __init__(self, index_name:str):
        self.idx = index.Index(index_name)
        self.r = get_redis()

    def add_box_to_index(self,id:int,  geo_fence_id:str, view:List[float], start_date:str, end_date:str):        
        metadata = {"start_date":start_date, "end_date":end_date, "geo_fence_id":geo_fence_id }        
        self.idx.insert(id = id, coordinates= (view[0], view[1], view[2], view[3]),obj = metadata)

    def delete_from_index(self,enumerated_id:int, view:List[float]):                
        self.idx.delete(id = enumerated_id, coordinates= (view[0], view[1], view[2], view[3]))

    def generate_geo_fence_index(self, all_fences:Union[QuerySet, List[GeoFence]]) -> None:
        """This method generates a rTree index of currently active operational indexes """      
        
        present = arrow.now()    
        start_date = present.shift(days=-1)
        end_date = present.shift(days=1)
        for fence_idx, fence in enumerate(all_fences):                                 
            fence_idx_str = str(fence.id)
            fence_id = int(hashlib.sha256(fence_idx_str.encode('utf-8')).hexdigest(), 16) % 10**8
            view = [float(i) for i in fence.bounds.split(",")]            
            self.add_box_to_index(id= fence_id, geo_fence_id = fence_idx_str, view = view, start_date=start_date.isoformat(), end_date= end_date.isoformat())

    def clear_rtree_index(self):
        """Method to delete all boxes from the index"""
        all_fences = GeoFence.objects.all()
        for fence_idx, fence in enumerate(all_fences):                                 
            fence_idx_str = str(fence.id)
            fence_id = int(hashlib.sha256(fence_idx_str.encode('utf-8')).hexdigest(), 16) % 10**8
            fence_bounds = fence.bounds
            view = [float(i) for i in fence_bounds.split(",")]                       

            self.delete_from_index(enumerated_id= fence_id,view = view)

    def check_box_intersection(self, view_box:List[float]):
        intersections = [n.object for n in self.idx.intersection((view_box[0], view_box[1], view_box[2], view_box[3]), objects=True)]        
        return intersections
