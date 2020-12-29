from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.utils.decorators import method_decorator
from auth_helper.utils import requires_scopes, BearerAuth
# Create your views here.
import json
import logging
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from .tasks import WriteFlightDeclaration



@api_view(['POST'])
@requires_scopes(['blender.write'])
def post_flight_declaration(request): 
    try:
        assert request.headers['Content-Type'] == 'application/json'   
    except AssertionError as ae:     
        msg = {"message":"Unsupported Media Type"}
        return JsonResponse(json.dumps(msg), status=415, mimetype='application/json')
    else:    
        req = json.loads(request.data)
        
    try:            
        flight_declaration_data = req["flight_declaration"]

    except KeyError as ke:
        msg = json.dumps({"message":"One parameter are required: observations with a list of observation objects. One or more of these were not found in your JSON request. For sample data see: https://github.com/openskies-sh/airtraffic-data-protocol-development/blob/master/Airtraffic-Data-Protocol.md#sample-traffic-object"})        
        return JsonResponse(msg, status=400, mimetype='application/json')

    else:
        task = WriteFlightDeclaration.delay(flight_declaration_data)  # Send a job to the task queuervation)  # Send a job to the task queue
        op = json.dumps ({"message":"Submitted Flight Declaration"})
        return JsonResponse(op, status=200, mimetype='application/json')

