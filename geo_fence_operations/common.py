import json

def validate_geo_zone(geo_zone) -> bool:
    '''A class to validate GeoZones '''
    

    if all(k in geo_zone for k in ("title","description",'features')):
        return True 

    else: 
        return False

