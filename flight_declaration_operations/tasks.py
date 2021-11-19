from celery.utils.log import get_task_logger
import logging
from . import flight_declaration_rw_helper
from flight_blender.celery import app

@app.task(name='write_flight_declaration')
def write_flight_declaration(fd):   
    my_credential_ops = flight_declaration_rw_helper.PassportCredentialsGetter()        
    fd_credentials = my_credential_ops.get_cached_credentials()
    

    try: 
        assert 'error' not in fd_credentials # Dictionary is populated 
    except AssertionError as e: 
        # Error in receiving a Flight Declaration credential
        logging.error('Error in getting Flight Declaration Token')
        logging.error(e)
    else:    
        my_uploader = flight_declaration_rw_helper.FlightDeclarationsUploader(credentials = fd_credentials)
        upload_status = my_uploader.upload_to_server(flight_declaration_json=fd)

        logging.info(upload_status)