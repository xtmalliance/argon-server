from django.dispatch import receiver
import django.dispatch
from django.core import management
from .operator_conformance_notifications import OperationConformanceNotification
import logging
from .conformance_state_helper import ConformanceChecksList
logger = logging.getLogger('django')
# Declare signals
telemetry_conformance_monitoring_signal = django.dispatch.Signal()
flight_authorization_conformance_monitoring_signal = django.dispatch.Signal()


@receiver(telemetry_conformance_monitoring_signal)
def process_telemetry_conformance_message(sender, **kwargs):  
    non_conformance_state = int(kwargs['non_conformance_state'])
    flight_declaration_id = kwargs['flight_declaration_id']
    my_operation_notification = OperationConformanceNotification(flight_declaration_id=flight_declaration_id)
    # Check the conformance notification status and notification rules     
    message = '{} -- {}'.format(sender, kwargs['non_conformance_state']) 
    
    non_conformance_state_code = ConformanceChecksList.state_code(non_conformance_state)
    
    if non_conformance_state_code == 'C3':        
        invalid_aircraft_id_msg = "The aircraft ID provided in telemetry for operation {flight_declaration_id}, does not match the declared / authorized aircraft, you must stop operation. C4 Check failed.".format(flight_declaration_id = flight_declaration_id)
        logging.error(invalid_aircraft_id_msg)
        my_operation_notification.send_conformance_status_notification(message = invalid_aircraft_id_msg, level='error')

    elif non_conformance_state_code in ['C4','C5']:        
        flight_state_not_correct_msg = "The Operation state for operation {flight_declaration_id}, is not one of 'Accepted' or 'Activated', your authorization is invalid. C4+C5 Check failed.".format(flight_declaration_id = flight_declaration_id)
        logging.error(flight_state_not_correct_msg)
        my_operation_notification.send_conformance_status_notification(message = flight_state_not_correct_msg, level='error')

    elif non_conformance_state_code == 'C6':        
        telemetry_timestamp_not_within_op_start_end_msg = "The telemetry timestamp provided for operation {flight_declaration_id}, is not within the start / end time for an operation. C6 Check failed.".format(flight_declaration_id = flight_declaration_id)
        logging.error(telemetry_timestamp_not_within_op_start_end_msg)
        my_operation_notification.send_conformance_status_notification(message = telemetry_timestamp_not_within_op_start_end_msg, level='error')

    elif non_conformance_state_code == 'C7a':        
        aircraft_altitude_nonconformant_msg = "The telemetry timestamp provided for operation {flight_declaration_id}, is not within the altitude bounds C7a check failed.".format(flight_declaration_id = flight_declaration_id)            
        logging.error(aircraft_altitude_nonconformant_msg)
        my_operation_notification.send_conformance_status_notification(message = aircraft_altitude_nonconformant_msg, level='error')

    elif non_conformance_state_code == 'C7b':
        aircraft_bounds_nonconformant_msg = "The telemetry location provided for operation {flight_declaration_id}, is not within the declared bounds for an operation. C7b check failed.".format(flight_declaration_id = flight_declaration_id)        
        logging.error(aircraft_bounds_nonconformant_msg)
        my_operation_notification.send_conformance_status_notification(message = aircraft_bounds_nonconformant_msg, level='error')
            
    # management.call_command('update_non_conforming_op_int_notify',flight_declaration_id = flight_declaration_id, dry_run =0)   
    

@receiver(flight_authorization_conformance_monitoring_signal)
def process_flight_authorization_conformance_message(sender, **kwargs):    
    non_conformance_state = kwargs['non_conformance_state']
    flight_declaration_id = kwargs['flight_declaration_id']
    my_operation_notification = OperationConformanceNotification(flight_declaration_id=flight_declaration_id)
    non_conformance_state_code = ConformanceChecksList.state_code(non_conformance_state)
      
    if non_conformance_state_code == 'C9a':
        telemetry_not_being_received_error_msg = "The telemetry for operation {flight_declaration_id}, has not been received in the past 15 seconds. Check C9a Failed".format(flight_declaration_id = flight_declaration_id)    
        my_operation_notification.send_conformance_status_notification(message = telemetry_not_being_received_error_msg, level='error')       
        # Declare state as contintgent because telemetry is not being received
        #TODO: Uncomment
        # management.call_command('operation_declares_contingency', flight_declaration_id = flight_declaration_id, dry_run = True)

    elif non_conformance_state_code == 'C9b':    
        telemetry_never_received_error_msg = "The telemetry for operation {flight_declaration_id}, has never been received. Check C9b Failed".format(flight_declaration_id = flight_declaration_id)            
        logging.error(telemetry_never_received_error_msg)
        my_operation_notification.send_conformance_status_notification(message = telemetry_never_received_error_msg, level='error')
        
        # Declare state as contintgent because telemetry is not being received
        #TODO: Uncomment
        # management.call_command('operation_declares_contingency', flight_declaration_id = flight_declaration_id, dry_run = True)
    elif non_conformance_state_code == 'C10':
        # notify the operator that the state of operation is not properly set. 
        
        flight_state_not_conformant = "The state for operation {flight_declaration_id}, has not been is not one of 'Activated', 'Nonconforming' or 'Contingent. Check C10 failed' ".format(flight_declaration_id = flight_declaration_id)            
        logging.error(flight_state_not_conformant)
        my_operation_notification.send_conformance_status_notification(message = flight_state_not_conformant, level='error')
        #TODO: Uncomment
        #management.call_command('operation_ended_clear_dss', flight_declaration_id = flight_declaration_id, dry_run = True)
    elif non_conformance_state_label =='C11':
        authorization_not_granted_message = "There is no flight authorization for operation with ID {flight_declaration_id}. Check C11 Failed".format(flight_declaration_id = flight_declaration_id)   
        logging.error(flight_state_not_conformant)
        # Flight Operation and Flight Authorization exists
        #TODO: Uncomment
        my_operation_notification.send_conformance_status_notification(message = authorization_not_granted_message, level='error')  
        

