from rest_framework import serializers
import json
from .models import SignedTelmetryPublicKey

class SignedTelmetryPublicKeySerializer(serializers.ModelSerializer):
    
    class Meta:
        model = SignedTelmetryPublicKey        
        fields = ('key_id','url', 'is_active',)
   