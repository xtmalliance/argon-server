from django.shortcuts import render
from django.utils.decorators import method_decorator
from auth_helper.utils import requires_scopes, BearerAuth
# Create your views here.
import json
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from .tasks import WriteGeoFence


@api_view(['POST'])
@requires_scopes(['blender.write'])
def post_geo_fence(request):   
    try:
        assert request.headers['Content-Type'] == 'application/json'   
    except AssertionError as ae:     
        msg = {"message":"Unsupported Media Type"}
        return JsonResponse(json.dumps(msg), status=415, mimetype='application/json')
    else:    
        geo_fence = json.loads(request.data)
    
    WriteGeoFence.delay(geo_fence)  # Send a job to the task queue

    op = json.dumps ({"message":"Geofence submitted successfully"})
    return JsonResponse(op, status=200, mimetype='application/json')
