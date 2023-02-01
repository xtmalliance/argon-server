from flight_blender.celery import app
from scd_operations.opint_helper import DSSOperationalIntentsCreator
from flight_declaration_operations.models import FlightDeclaration
import logging
logger = logging.getLogger('django')
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

@app.task(name='submit_flight_declaration_to_dss')
def submit_flight_declaration_to_dss(flight_declaration_id:str):

    my_dss_opint_creator = DSSOperationalIntentsCreator(flight_declaration_id)
    
    flight_operation_validated = my_dss_opint_creator.validate_flight_declaration_details()
    
    logging.info("Flight Operation Validation status %s"% flight_operation_validated)
    if flight_operation_validated:            
        opint_submission_result = my_dss_opint_creator.submit_flight_declaration_to_dss()            
        if opint_submission_result.status_code == 500:
            logger.error("Error in submitting Flight Declaration to the DSS %s" % opint_submission_result.status)
        elif opint_submission_result.status_code in [200, 201]:
            logger.info("Successfully submitted Flight Declaration to the DSS %s" % opint_submission_result.status)
            
            fo = FlightDeclaration.objects.get(id = flight_declaration_id)
            # Update state of the flight operation
            fo.state = 1
            fo.save()
        logging.info("Details of the submission status %s" % opint_submission_result.message)
    else:            
        logging.error("Flight Declaration details are not valid, please check the submitted GeoJSON, this operation will not be sent to the DSS for strategic deconfliction")

