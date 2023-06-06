from django.db import models
import uuid
from datetime import datetime
from django.utils.translation import gettext_lazy as _
from common.data_definitions import OPERATION_STATES, OPERATION_TYPES

class FlightDeclaration(models.Model):
    ''' A flight operation object for permission '''     
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    operational_intent = models.TextField()
    flight_declaration_raw_geojson = models.TextField(null=True, blank=True)
    type_of_operation = models.IntegerField(choices=OPERATION_TYPES, default=1, help_text="At the moment, only VLOS and BVLOS operations are supported, for other types of operations, please issue a pull-request")
    bounds = models.CharField(max_length = 140)
    aircraft_id = models.CharField(max_length=256, default='000', help_text="Specify the ID of the aircraft for this declaration")    
    state = models.IntegerField(choices=OPERATION_STATES, default=0, help_text="Set the state of operation")

    originating_party = models.CharField(max_length=100, help_text="Set the party originating this flight, you can add details e.g. Aerobridge Flight 105", default="Flight Blender Default")

    submitted_by = models.EmailField(blank= True, null= True)
    approved_by = models.EmailField(blank= True, null= True)
    
    latest_telemetry_datetime = models.DateTimeField(help_text="The time at which the last telemetry was received for this operation, this is used to determine operational conformance",blank= True, null= True)

    start_datetime = models.DateTimeField(default=datetime.now)
    end_datetime = models.DateTimeField(default=datetime.now)

    is_approved = models.BooleanField(default =False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        
    def __unicode__(self):
       return self.originating_party + ' ' + str(self.id)

    def __str__(self):
        return self.originating_party + ' ' + str(self.id)
        
class FlightAuthorization(models.Model):   
    """ This object hold the associated """ 
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    declaration = models.OneToOneField(FlightDeclaration, on_delete= models.CASCADE)
    dss_operational_intent_id = models.CharField(max_length = 36, blank=True, null= True, help_text="Once the operational intent is shared on the DSS the operational intent is is stored here. By default nothing is stored here.")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
        
    def __unicode__(self):
       return "Authorization for " + self.declaration

    class Meta:
        ordering = ['-created_at']