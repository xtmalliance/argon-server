import uuid

from django.db import models


class PublicKey(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key_id = models.TextField(help_text="Specify the Key ID")
    url = models.URLField(help_text="Enter the JWK / JWKS URL of the public key")
    is_active = models.BooleanField(
        default=True,
        help_text="Specify if the key is active, only active keys will be validated against",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Key :" + self.url
