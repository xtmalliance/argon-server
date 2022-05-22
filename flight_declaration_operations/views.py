# Create your views here.
from django.shortcuts import render
from auth_helper.utils import requires_scopes
# Create your views here.
import json
import arrow
from rest_framework.decorators import api_view
import logging
from django.http import HttpResponse, JsonResponse
from .models import FlightOperation
from .tasks import write_flight_declaration
from shapely.geometry import asShape
from shapely.ops import unary_union
from django.http import Http404
from rest_framework import mixins, generics
from .serializers import FlightOperationSerializer, FlightOperationApprovalSerializer
from django.utils.decorators import method_decorator
from django.utils import timezone
from datetime import datetime, timedelta
from datetime import date
from django.utils.timezone import make_aware


@api_view(['POST'])
@requires_scopes(['blender.write'])
def set_flight_declaration(request): 
    try:
        assert request.headers['Content-Type'] == 'application/json'   
    except AssertionError as ae:     
        msg = {"message":"Unsupported Media Type"}
        return JsonResponse(json.dumps(msg), status=415, mimetype='application/json')
    else:    
        req = request.data
    try:            
        flight_declaration_data = req["flight_declaration"]

    except KeyError as ke:
        msg = json.dumps({"message":"One parameter are required: observations with a list of observation objects. One or more of these were not found in your JSON request. For sample data see: https://github.com/openskies-sh/airtraffic-data-protocol-development/blob/master/Airtraffic-Data-Protocol.md#sample-traffic-object"})        
        return HttpResponse(msg, status=400)

    else:
        # task = write_flight_declaration.delay(json.dumps(flight_declaration_data))  # Send a job to spotlight
        geo_json_fc = flight_declaration_data['flight_declaration']['parts']
        shp_features = []
        for feature in geo_json_fc['features']:
            shp_features.append(asShape(feature['geometry']))
        combined_features = unary_union(shp_features)
        bnd_tuple = combined_features.bounds
        bounds = ''.join(['{:.7f}'.format(x) for x in bnd_tuple])
        try:
            req["start_time"]
        except KeyError as ke: 
            start_time = arrow.now().isoformat()
        else:
            start_time = arrow.get(req["start_time"]).isoformat()
        
        try:
            req["end_time"]
        except KeyError as ke:
            end_time = arrow.now().shift(hours=1).isoformat()
        else:
            
            end_time = arrow.get(req["end_time"]).isoformat()
        
        type_of_operation = flight_declaration_data['operation_mode']
        type_of_operation = 1  if (type_of_operation =='bvlos') else 0
        fo = FlightOperation(gutma_flight_declaration = json.dumps(flight_declaration_data),start_datetime= start_time, end_datetime=end_time, bounds= bounds, type_of_operation= type_of_operation)
        fo.save()
        
        op = json.dumps ({"message":"Submitted Flight Declaration", 'id':str(fo.id), 'is_approved':0})
        return HttpResponse(op, status=200)


@method_decorator(requires_scopes(['blender.read']), name='dispatch')
class FlightOperationApproval( 
                    mixins.UpdateModelMixin,           
                    generics.GenericAPIView):

    queryset = FlightOperation.objects.all()
    serializer_class = FlightOperationApprovalSerializer


    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


@method_decorator(requires_scopes(['blender.read']), name='dispatch')
class FlightOperationDetail(mixins.RetrieveModelMixin, 
                    generics.GenericAPIView):

    queryset = FlightOperation.objects.all()
    serializer_class = FlightOperationSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

@method_decorator(requires_scopes(['blender.read']), name='dispatch')
class FlightOperationList(mixins.ListModelMixin,  
    generics.GenericAPIView):

    queryset = FlightOperation.objects.all()
    serializer_class = FlightOperationSerializer

    def get_responses(self, start, end):
        
        present = arrow.now()
        if start and end:
            start_date = arrow.get(start, "YYYY-MM-DD")
            end_date = arrow.get(end, "YYYY-MM-DD")
    
        else: 
            
            start_date = present.shift(months=-1)
            end_date = present.shift(days=1)
        
        return FlightOperation.objects.filter(start_datetime__gte = start_date.isoformat(), end_datetime__lte = end_date.isoformat())

    def get_queryset(self):
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)

        Responses = self.get_responses(start_date, end_date)
        return Responses

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)