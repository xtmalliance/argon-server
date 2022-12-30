# Create your views here.
import uuid
from auth_helper.utils import requires_scopes
# Create your views here.
import json
import arrow
from typing import List
from . import rtree_geo_fence_helper
from rest_framework.decorators import api_view
from shapely.geometry import shape
from .models import GeoFence
from django.http import HttpResponse
from .tasks import write_geo_zone
from shapely.ops import unary_union
from rest_framework import mixins, generics
from .serializers import GeoFenceSerializer
from django.utils.decorators import method_decorator
from decimal import Decimal
import logging
logger = logging.getLogger('django')


INDEX_NAME = 'geofence_proc'

@api_view(['POST'])
@requires_scopes(['blender.write'])
def set_geo_fence(request):  
    
    try:
        assert request.headers['Content-Type'] == 'application/json'   
    except AssertionError as ae:     
        msg = {"message":"Unsupported Media Type"}
        return HttpResponse(json.dumps(msg), status=415, mimetype='application/json')

    try:         
        geo_json_fc = request.data
    except KeyError as ke: 
        msg = json.dumps({"message":"A geofence object is necessary in the body of the request"})        
        return HttpResponse(msg, status=400)    

    shp_features = []
    for feature in geo_json_fc['features']:
        shp_features.append(shape(feature['geometry']))
    combined_features = unary_union(shp_features)
    bnd_tuple = combined_features.bounds
    bounds = ''.join(['{:.7f}'.format(x) for x in bnd_tuple])
    try:
        s_time = geo_json_fc[0]['properties']["start_time"]
    except KeyError as ke: 
        start_time = arrow.now().isoformat()
    else:
        start_time = arrow.get(s_time).isoformat()
    
    try:
        e_time = geo_json_fc[0]['properties']["end_time"]
    except KeyError as ke:
        end_time = arrow.now().shift(hours=1).isoformat()
    else:            
        end_time = arrow.get(e_time).isoformat()

    try:
        upper_limit = Decimal(geo_json_fc[0]['properties']["upper_limit"])
    except KeyError as ke: 
        upper_limit = 500.00
    
    try:
        lower_limit = Decimal(geo_json_fc[0]['properties']["upper_limit"])
    except KeyError as ke:
        lower_limit = 100.00
             
    try:
        name = geo_json_fc[0]['properties']["name"]
    except KeyError as ke:
        name = "Standard Geofence"
    raw_geo_fence = json.dumps(geo_json_fc)
    geo_f = GeoFence(raw_geo_fence = raw_geo_fence,start_datetime = start_time, end_datetime = end_time, upper_limit= upper_limit, lower_limit=lower_limit, bounds= bounds, name= name)
    geo_f.save()

    op = json.dumps ({"message":"Geofence Declaration submitted", 'id':str(geo_f.id)})
    return HttpResponse(op, status=200)

@api_view(['POST'])
@requires_scopes(['blender.write'])
def set_geozone(request):  
    try:
        assert request.headers['Content-Type'] == 'application/json'   
    except AssertionError as ae:     
        msg = {"message":"Unsupported Media Type"}
        return HttpResponse(json.dumps(msg), status=415, mimetype='application/json')

    try:         
        geo_zone = request.data
    except KeyError as ke: 
        msg = json.dumps({"message":"A geozone object is necessary in the body of the request"})        
        return HttpResponse(msg, status=400)    


    if 'title' not in geo_zone:
        msg = json.dumps({"message":"A geozone object with a title is necessary the body of the request"})        
        return HttpResponse(msg, status=400)   

    if 'description' not in geo_zone:
        msg = json.dumps({"message":"A geozone object with a description is necessary the body of the request"})        
        return HttpResponse(msg, status=400)   


    if 'features' in geo_zone:
        geo_zone_features = geo_zone['features']
    else: 
        geo_zone_features = []
    
    write_geo_zone.delay(geo_zone = json.dumps(geo_zone))
    
    geo_f = uuid.uuid4()
    op = json.dumps ({"message":"Geofence Declaration submitted", 'id':str(geo_f)})
    return HttpResponse(op, status=200)

@method_decorator(requires_scopes(['blender.read']), name='dispatch')
class GeoFenceDetail(mixins.RetrieveModelMixin, 
                    generics.GenericAPIView):

    queryset = GeoFence.objects.all()
    serializer_class = GeoFenceSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

@method_decorator(requires_scopes(['blender.read']), name='dispatch')
class GeoFenceList(mixins.ListModelMixin,  
    generics.GenericAPIView):

    queryset = GeoFence.objects.all()
    serializer_class = GeoFenceSerializer

    def get_relevant_geo_fence(self,start_date, end_date,  view_port:List[float]):               


        present = arrow.now()
        if start_date and end_date:
            s_date = arrow.get(start_date, "YYYY-MM-DD")
            e_date = arrow.get(end_date, "YYYY-MM-DD")
    
        else:             
            s_date = present.shift(days=-1)
            e_date = present.shift(days=1)

        all_fences_within_timelimits = GeoFence.objects.filter(start_datetime__lte = s_date.isoformat(), end_datetime__gte = e_date.isoformat())
        logging.info("Found %s geofences" % len(all_fences_within_timelimits))
        if view_port:
            
            my_rtree_helper = rtree_geo_fence_helper.GeoFenceRTreeIndexFactory()  
            my_rtree_helper.generate_geo_fence_index(all_fences = all_fences_within_timelimits)
            all_relevant_fences = my_rtree_helper.check_box_intersection(view_box = view_port)
            relevant_id_set = []
            for i in all_relevant_fences:
                relevant_id_set.append(i['geo_fence_id'])

            my_rtree_helper.clear_rtree_index()
            filtered_relevant_fences = GeoFence.objects.filter(id__in = relevant_id_set)
            
        else: 
            filtered_relevant_fences = all_fences_within_timelimits

        return filtered_relevant_fences

    def get_queryset(self):
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)

        view = self.request.query_params.get('view', None)
        view_port = []
        if view:
            view_port = [float(i) for i in view.split(",")]
        
        responses = self.get_relevant_geo_fence(view_port= view_port,start_date= start_date, end_date= end_date)
        return responses

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

        