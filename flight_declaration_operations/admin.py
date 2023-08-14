from django.contrib import admin
from .models import FlightDeclaration, FlightAuthorization

# Register your models here.

admin.site.register(FlightDeclaration)
admin.site.register(FlightAuthorization)