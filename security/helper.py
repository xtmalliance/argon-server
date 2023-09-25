import base64
import json
from urllib.parse import urlparse

import cryptography.hazmat.primitives.serialization as serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from django.http import HttpRequest
from requests import Request

def get_jwk_from_public_pem_key(path: str):
    # Load the public key in PEM format
    with open(path, "rb") as key_file:
        pem_data = key_file.read()
    # Convert PEM to a public key object
    public_key = serialization.load_pem_public_key(pem_data, backend=default_backend())

    # Extract the public key components
    if isinstance(public_key, rsa.RSAPublicKey):
        key_type = "RSA"
        jwk_dict = {
            "kty": key_type,
            "n": base64.urlsafe_b64encode(
                public_key.public_numbers().n.to_bytes(
                    (public_key.public_numbers().n.bit_length() + 7) // 8,
                    byteorder="big",
                )
            )
            .rstrip(b"=")
            .decode("utf-8"),
            "e": base64.urlsafe_b64encode(
                public_key.public_numbers().e.to_bytes(
                    (public_key.public_numbers().e.bit_length() + 7) // 8,
                    byteorder="big",
                )
            )
            .rstrip(b"=")
            .decode("utf-8"),
        }
    elif isinstance(public_key, ec.EllipticCurvePublicKey):
        key_type = "EC"
        curve_name = public_key.curve.name
        x_bytes = public_key.public_numbers().x.to_bytes(
            (public_key.curve.key_size + 7) // 8, byteorder="big"
        )
        y_bytes = public_key.public_numbers().y.to_bytes(
            (public_key.curve.key_size + 7) // 8, byteorder="big"
        )
        jwk_dict = {
            "kty": key_type,
            "crv": curve_name,
            "x": base64.urlsafe_b64encode(x_bytes).rstrip(b"=").decode("utf-8"),
            "y": base64.urlsafe_b64encode(y_bytes).rstrip(b"=").decode("utf-8"),
        }
    else:
        raise ValueError("Unsupported key type")

    # Output the JWK as a JSON string
    jwk_json = json.dumps(jwk_dict, indent=4)

    return jwk_json


def http_request_to_django_request(request: Request) -> HttpRequest:
    """
    Convert Request to Django Request object
    """

    parsed_url = urlparse(request.url)
    server_name = parsed_url.hostname
    server_port = parsed_url.port if parsed_url.port else 80

    django_request = HttpRequest()
    django_request.method = request.method
    django_request.path = request.path_url
    django_request.META["SERVER_NAME"] = server_name
    django_request.META["SERVER_PORT"] = server_port

    for key, value in request.headers.items():
        django_request.META["HTTP_" + key.upper().replace("-", "_")] = value
    if request.body:
        django_request.data = request.body
    return django_request
