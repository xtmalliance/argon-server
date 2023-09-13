import json
from functools import wraps
from os import environ as env

import jwt
import requests
from django.contrib.auth import authenticate
from django.http import JsonResponse
from dotenv import find_dotenv, load_dotenv
from rest_framework import status

load_dotenv(find_dotenv())


def jwt_get_username_from_payload_handler(payload):
    username = payload.get("sub").replace("|", ".")
    authenticate(remote_user=username)
    return username


def requires_scopes(required_scopes):
    """Determines if the required scope is present in the access token
    Args:
        required_scopes (list): The scopes required to access the resource
    """

    s = requests.Session()

    def require_scope(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            request = args[0]
            auth: str = request.META.get("HTTP_AUTHORIZATION", None)

            if not auth:
                return JsonResponse(
                    {"detail": "Authentication credentials were not provided"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            parts = auth.split()
            if len(parts) != 2:
                return JsonResponse(
                    {"detail": "Authentication credentials are in incorrect form"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            token = parts[1]

            API_IDENTIFIER = env.get(
                "PASSPORT_AUDIENCE", "testflight.flightblender.com"
            )
            try:
                unverified_token_headers = jwt.get_unverified_header(token)
            except jwt.exceptions.DecodeError:
                return JsonResponse(
                    {"detail": "Bearer token could not be decoded properly"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            if "kid" not in unverified_token_headers:
                # This is for testing DSS locally
                token_details = jwt.decode(
                    token, algorithms=["RS256"], options={"verify_signature": False}
                )

                if "iss" in token_details.keys() and token_details["iss"] in [
                    "dummy",
                    "NoAuth",
                ]:
                    return f(*args, **kwargs)
                else:
                    return JsonResponse(
                        {"detail": "Invalid token provided"},
                        status=status.HTTP_401_UNAUTHORIZED,
                    )

            PASSPORT_URL = "{}/.well-known/jwks.json".format(
                env.get("PASSPORT_URL", "http://local.test:9000")
            )
            try:
                jwks = s.get(PASSPORT_URL).json()
            except requests.exceptions.RequestException:
                return JsonResponse(
                    {
                        "detail": "Public Key Server to validate the token could not be reached"
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            public_keys = {}
            for jwk in jwks["keys"]:
                kid = jwk["kid"]
                public_keys[kid] = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
            try:
                kid = unverified_token_headers["kid"]
            except (KeyError, ValueError):
                return JsonResponse(
                    {
                        "detail": "Invalid public key details in token / token cannot be verified"
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            else:
                try:
                    assert kid in public_keys
                except AssertionError:
                    return JsonResponse(
                        {
                            "detail": "Invalid public key details in token / token cannot be verified"
                        },
                        status=status.HTTP_401_UNAUTHORIZED,
                    )
                else:
                    public_key = public_keys[kid]

            try:
                decoded = jwt.decode(
                    token, public_key, audience=API_IDENTIFIER, algorithms=["RS256"]
                )
            except jwt.ImmatureSignatureError:
                return JsonResponse(
                    {"detail": "Token Signature has is not valid"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            except jwt.ExpiredSignatureError:
                return JsonResponse(
                    {"detail": "Token Signature has expired"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            except jwt.InvalidAudienceError:
                return JsonResponse(
                    {"detail": "Invalid audience in token"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            except jwt.InvalidIssuerError:
                return JsonResponse(
                    {"detail": "Invalid issuer for token"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            except jwt.InvalidSignatureError:
                return JsonResponse(
                    {"detail": "Invalid signature in token"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            except jwt.DecodeError:
                return JsonResponse(
                    {"detail": "Token cannot be decoded"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            except Exception:
                return JsonResponse(
                    {"detail": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED
                )

            if decoded.get("scope"):
                token_scopes = decoded["scope"].split()
                token_scopes_set = set(token_scopes)
                if set(required_scopes).issubset(token_scopes_set):
                    return f(*args, **kwargs)
            return JsonResponse(
                {"message": "You don't have access to this resource"},
                status=status.HTTP_403_FORBIDDEN,
            )

        return decorated

    return require_scope


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r
