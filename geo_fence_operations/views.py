# Create your views here.
import uuid
from auth_helper.utils import requires_scopes
# Create your views here.
import json
import arrow
from rest_framework.decorators import api_view

from django.http import HttpResponse
from .models import GeoFence
from .tasks import write_geo_fence
from shapely.geometry import asShape, Point, mapping
from shapely.ops import unary_union

from .data_definitions import ImplicitDict, ZoneAuthority, HorizontalProjection, ED269Geometry, GeoZoneFeature, GeoZone
from rest_framework import mixins, generics
from .serializers import GeoFenceSerializer
from django.utils.decorators import method_decorator
from decimal import Decimal

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
        shp_features.append(asShape(feature['geometry']))
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

    write_geo_fence.delay(geo_fence = raw_geo_fence)
    

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

    for _geo_zone_feature in geo_zone_features:
        zone_authorities = _geo_zone_feature['zoneAuthority']
        all_zone_authorities = []
        for z_a in zone_authorities:
            zone_authority = ImplicitDict.parse(z_a, ZoneAuthority)
            all_zone_authorities.append(zone_authority)
        ed_269_geometries = []
        
        all_ed_269_geometries = _geo_zone_feature['geometry']
        for ed_269_geometry in all_ed_269_geometries:
            if (ed_269_geometry['horizontalProjection']['type']=='Polygon'):
                horizontal_projection = ImplicitDict.parse(ed_269_geometry['horizontalProjection'], HorizontalProjection)    

            elif (ed_269_geometry['horizontalProjection']['type']=='Circle'):
                lat = ed_269_geometry['horizontalProjection']['center'][1]
                lng = ed_269_geometry['horizontalProjection']['center'][0]
                radius = ed_269_geometry['horizontalProjection']['radius']

                p = Point(lng, lat)
                buf = p.buffer(radius)
                geo_json = mapping(buf)               



            ed_269_geometry = ED269Geometry(uomDimensions =ed_269_geometry['uomDimensions'],lowerLimit= ed_269_geometry['lowerLimit'],lowerVerticalReference=ed_269_geometry['lowerVerticalReference'], upperLimit=ed_269_geometry['upperLimit'], upperVerticalReference=ed_269_geometry['upperVerticalReference'], horizontalProjection= horizontal_projection)
            ed_269_geometries.append(ed_269_geometry)
        
        geo_zone_feature = GeoZoneFeature(identifier= _geo_zone_feature['identifier'], country= _geo_zone_feature['country'],name= _geo_zone_feature['name'],type= _geo_zone_feature['type'], restriction=_geo_zone_feature['restriction'] ,restrictionConditions=_geo_zone_feature['restrictionConditions'], region=_geo_zone_feature['region'], reason = _geo_zone_feature['reason'], otherReasonInfo=_geo_zone_feature['otherReasonInfo'] ,regulationExemption=_geo_zone_feature['regulationExemption'], uSpaceClass=_geo_zone_feature['uSpaceClass'], message =_geo_zone_feature['message'] , applicability=_geo_zone_feature['applicability'], zoneAuthority = all_zone_authorities , geometry = ed_269_geometries)
        geo_zone_features.append(geo_zone_feature)
    

    geo_zone = GeoZone(title= geo_zone['title'], description = geo_zone['description'],  features = geo_zone_features)

    print(json.dumps(geo_zone))
    # geo_f = GeoFence(geo_zone = geo_zone,start_datetime = start_time, end_datetime = end_time, upper_limit= upper_limit, lower_limit=lower_limit, bounds= bounds, name= name)
    # geo_f.save()



    # write_geo_fence.delay(geo_fence = raw_geo_fence)
    
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