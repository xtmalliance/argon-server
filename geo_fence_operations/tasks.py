from flight_blender.celery import app
import logging
import json
from typing import List
from .data_definitions import ImplicitDict, ZoneAuthority, HorizontalProjection, ED269Geometry, GeoZoneFeature, GeoZone
from shapely.geometry import shape, Point, mapping
from functools import partial
import pyproj
from shapely.ops import transform
import arrow
from .models import GeoFence
from shapely.ops import unary_union
logger = logging.getLogger('django')

proj_wgs84 = pyproj.Proj('+proj=longlat +datum=WGS84')


def geodesic_point_buffer(lat, lon, km):
    # Azimuthal equidistant projection
    aeqd_proj = '+proj=aeqd +lat_0={lat} +lon_0={lon} +x_0=0 +y_0=0'
    project = partial(
        pyproj.transform,
        pyproj.Proj(aeqd_proj.format(lat=lat, lon=lon)),
        proj_wgs84)
    buf = Point(0, 0).buffer(km * 1000)  # distance in metres
    return transform(project, buf)


@app.task(name="write_geo_zone")
def write_geo_zone(geo_zone): 

    geo_zone = json.loads(geo_zone)
    processed_geo_zone_features: List[GeoZoneFeature] = []
    
    for _geo_zone_feature in geo_zone['features']:
        zone_authorities = _geo_zone_feature['zoneAuthority']
        all_zone_authorities = []
        for z_a in zone_authorities:
            zone_authority = ImplicitDict.parse(z_a, ZoneAuthority)
            all_zone_authorities.append(zone_authority)
        ed_269_geometries = []
        
        all_ed_269_geometries = _geo_zone_feature['geometry']
        
        for ed_269_geometry in all_ed_269_geometries:
            parse_error = False
            if (ed_269_geometry['horizontalProjection']['type']=='Polygon'):
                pass
            elif (ed_269_geometry['horizontalProjection']['type']=='Circle'):
                try:
                    lat = ed_269_geometry['horizontalProjection']['center'][1]
                    lng = ed_269_geometry['horizontalProjection']['center'][0]
                    radius = ed_269_geometry['horizontalProjection']['radius']
                except KeyError as ke: 
                    logging.info("Error in parsing points provided in the ED 269 file %s" %ke)
                    
                    parse_error = True
                else:
                    r = radius / 1000 # Radius in km                
                    buf = geodesic_point_buffer(lat, lng, r)
                    b = mapping(buf)                
                    fc = {"type":"FeatureCollection","features":[ {"type": "Feature", "properties": {}, "geometry":b}]}
                    logging.info("Converting point to circle")
                    # logging.info(json.dumps(fc))
                    ed_269_geometry['horizontalProjection'] = b
            if not parse_error: 
                horizontal_projection = ImplicitDict.parse(ed_269_geometry['horizontalProjection'], HorizontalProjection)    
                parse_error = False
                ed_269_geometry = ED269Geometry(uomDimensions =ed_269_geometry['uomDimensions'],lowerLimit= ed_269_geometry['lowerLimit'],lowerVerticalReference=ed_269_geometry['lowerVerticalReference'], upperLimit=ed_269_geometry['upperLimit'], upperVerticalReference=ed_269_geometry['upperVerticalReference'], horizontalProjection= horizontal_projection)
                ed_269_geometries.append(ed_269_geometry)
        
        
        geo_zone_feature = GeoZoneFeature(identifier= _geo_zone_feature['identifier'], country= _geo_zone_feature['country'],name= _geo_zone_feature['name'],type= _geo_zone_feature['type'], restriction=_geo_zone_feature['restriction'] ,restrictionConditions=_geo_zone_feature['restrictionConditions'], region=_geo_zone_feature['region'], reason = _geo_zone_feature['reason'], otherReasonInfo=_geo_zone_feature['otherReasonInfo'] ,regulationExemption=_geo_zone_feature['regulationExemption'], uSpaceClass=_geo_zone_feature['uSpaceClass'], message =_geo_zone_feature['message'] , applicability=_geo_zone_feature['applicability'], zoneAuthority = all_zone_authorities , geometry = ed_269_geometries)
        processed_geo_zone_features.append(geo_zone_feature)
    logging.info("Processing %s geozone features.." %len(processed_geo_zone_features) )
    for geo_zone_feature in processed_geo_zone_features:
        all_feat_geoms = geo_zone_feature.geometry

        fc = {"type":"FeatureCollection","features":[]}
        all_shapes = []
        for g in all_feat_geoms:
            f = {"type": "Feature", "properties": {}, "geometry":{}}
            s = shape(g['horizontalProjection'])
            f['geometry'] = g['horizontalProjection']
            fc['features'].append(f)
            all_shapes.append(s)
        u = unary_union(all_shapes)
        bounds = u.bounds
        bounds_str = ','.join([str(x) for x in bounds])
        
        logging.debug("Bounding box for shape..")
        logging.debug(bounds)
        geo_zone = GeoZone(title= geo_zone['title'], description = geo_zone['description'],  features = geo_zone_feature)
        name = geo_zone_feature.name 
        # print(json.dumps(geo_zone_feature))
        start_time = arrow.now()
        end_time = start_time.shift(years =1)
        upper_limit = geo_zone_feature['upperLimit'] if 'upperLimit' in geo_zone_feature else 300
        lower_limit = geo_zone_feature['lowerLimit'] if 'lowerLimit' in geo_zone_feature else 10
        geo_f = GeoFence(geozone = json.dumps(geo_zone_feature),raw_geo_fence= json.dumps(fc), start_datetime = start_time.isoformat(), end_datetime = end_time.isoformat(), upper_limit=upper_limit, lower_limit=lower_limit, bounds= bounds_str, name= name)
        geo_f.save()

        logging.info("Saved Geofence to database ..")