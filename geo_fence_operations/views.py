# Create your views here.
from django.shortcuts import render
from auth_helper.utils import requires_scopes, BearerAuth
# Create your views here.
import json
import arrow
from rest_framework.decorators import api_view
import logging
from django.http import HttpResponse, JsonResponse
from .models import GeoFence
from .tasks import write_geo_fence
from shapely.geometry import asShape
from shapely.ops import unary_union
from django.http import Http404
from rest_framework import mixins, generics
from .serializers import GeoFenceSerializer
from django.utils.decorators import method_decorator
from django.utils import timezone
from datetime import datetime, timedelta
from datetime import date
from django.utils.timezone import make_aware


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
    else:    
        gf = json.dumps(geo_json_fc)
        # write_geo_fence.delay(gf)  # Send a job to the task queue

        geo_json_fc = geo_fence
        shp_features = []
        for feature in geo_json_fc['features']:
            shp_features.append(asShape(feature['geometry']))
        combined_features = unary_union(shp_features)
        bnd_tuple = combined_features.bounds
        bounds = ''.join(['{:.7f}'.format(x) for x in bnd_tuple])
        try:
            s_time = geo_json_fc[0]['properties']["start_time"]
        except KeyError as ke: 
            start_time = arrow.now().isoformat()
        else:
            start_time = arrow.get(req["s_time"]).isoformat()
        
        try:
            e_time = geo_json_fc[0]['properties']["end_time"]
        except KeyError as ke:
            end_time = arrow.now().shift(hours=1).isoformat()
        else:            
            end_time = arrow.get(e_time).isoformat()
                  
        
        geo_f = GeoFence(raw_geo_fence = json.dumps(flight_declaration_data),start_datetime = start_time, end_datetime = end_time, upper_limit= upper_limit, lower_limit=lower_limit, bounds= bounds, name= name)
        geo_f.save()
        
        op = json.dumps ({"message":"Geofence Declaration submitted", 'id':str(geo_f.id)})
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

    def get_responses(self, start, end):
        
        present = arrow.now()
        if start and end:
            start_date = arrow.get(start, "YYYY-MM-DD")
            end_date = arrow.get(end, "YYYY-MM-DD")
    
        else: 
            
            start_date = present.shift(months=-1)
            end_date = present.shift(days=1)
        
        return GeoFence.objects.filter(start_datetime__gte = start_date.isoformat(), end_datetime__lte = end_date.isoformat())

    def get_queryset(self):
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)

        Responses = self.get_responses(start_date, end_date)
        return Responses

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)