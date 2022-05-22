from flight_blender.celery import app
import logging
from . import geo_fence_rw_helper


@app.task(name="write_geo_fence")
def write_geo_fence(geo_fence): 
    my_credentials = geo_fence_rw_helper.PassportCredentialsGetter()
    gf_credentials = my_credentials.get_cached_credentials()
    try: 
        assert 'error' not in gf_credentials # Credentials dictionary is populated
    except AssertionError as ae: 
        # Error in getting a Geofence credentials getting
        logging.error('Error in getting Geofence Token')
        logging.error(ae)
    else:
        my_uploader = geo_fence_rw_helper.GeoFenceUploader(credentials = gf_credentials)
        upload_status = my_uploader.upload_to_server(gf=geo_fence)
        logging.info(upload_status)