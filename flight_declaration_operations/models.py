from django.db import models
import uuid
from datetime import datetime
import random, string
from django.utils.translation import ugettext_lazy as _

def make_random_plan_common_name():
    length = 2
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return  "Flight " + result_str


# Create your models here.
class FlightPlan(models.Model):
    ''' This is a model to hold flight plan in a GUTMA Flight Declaration format '''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=30, default=  make_random_plan_common_name)
    details = models.TextField(null=True, help_text="Paste flight plan geometry")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __unicode__(self):
       return self.name

    def __str__(self):
        return self.name 

    
class FlightOperation(models.Model):
    ''' A flight operation object for permission ''' 
    OPERATION_TYPES = ((0, _('VLOS')),(1, _('BVLOS')),)
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    operator_name = models.CharField(max_length=280, default="No operator provided", help_text="Enter name of your company")
    name = models.CharField(max_length=30, default= make_random_plan_common_name)
    flight_plan = models.ForeignKey(FlightPlan, models.CASCADE)
    type_of_operation = models.IntegerField(choices=OPERATION_TYPES, default=0, help_text="At the moment, only VLOS and BVLOS operations are supported, for other types of operations, please issue a pull-request")
    
    flight_termination_or_return_home_capability = models.BooleanField(default =1)
    geo_fencing_capability = models.BooleanField(default =1)
    detect_and_avoid_capability= models.BooleanField(default =0)
    
    start_datetime = models.DateTimeField(default=datetime.now)
    end_datetime = models.DateTimeField(default=datetime.now)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
       return self.name + ' ' + self.flight_plan.name

    def __str__(self):
        return self.name + ' ' + self.flight_plan.name
