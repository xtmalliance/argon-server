from django.contrib import admin

from .models import FlightAuthorization, FlightDeclaration

# Register your models here.

admin.site.register(FlightDeclaration)
admin.site.register(FlightAuthorization)
