from django.db import models
import uuid
from datetime import datetime
from django.utils.translation import gettext_lazy as _


class GeoFence(models.Model):
    ''' A model for Geofence storage in Flight Blender''' 

    ALTITUDE_REF = ((0, _('WGS84')),(1, _('AGL')),(2, _('MSL')),)
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    raw_geo_fence = models.TextField()

    upper_limit = models.DecimalField(max_digits=6, decimal_places=2)
    lower_limit = models.DecimalField(max_digits=6, decimal_places=2)

    altitude_ref = models.IntegerField(choices=ALTITUDE_REF, default=0)
    
    name = models.CharField(max_length = 50)
    bounds = models.CharField(max_length = 140)

    start_datetime = models.DateTimeField(default=datetime.now)
    end_datetime = models.DateTimeField(default=datetime.now)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __unicode__(self):
       return self.name

    def __str__(self):
        return self.name
