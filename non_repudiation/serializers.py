from rest_framework import serializers

from .models import PublicKey


class PublicKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicKey
        fields = (
            "key_id",
            "url",
            "is_active",
        )
