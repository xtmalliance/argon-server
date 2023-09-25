import hashlib
import json
import logging
from os import environ as env

import http_sfv
import jwt
import requests
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.backends import default_backend
from django.core.signing import Signer
from django.http import HttpRequest, HttpResponse
from dotenv import find_dotenv, load_dotenv
from http_message_signatures import (
    HTTPMessageSigner,
    HTTPMessageVerifier,
    HTTPSignatureKeyResolver,
    algorithms,
)
from jwcrypto import jwk, jws
from jwcrypto.common import json_encode

import security.helper as helper
from auth_helper.common import get_redis
from non_repudiation.models import PublicKey

load_dotenv(find_dotenv())


logger = logging.getLogger("django")


class BlenderHTTPSignatureKeyResolver(HTTPSignatureKeyResolver):
    def __init__(self, jwk):
        self.jwk = jwk

    def resolve_public_key(self, key_id: str):
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(self.jwk)
        return public_key

    def resolve_private_key(self, key_id: str):
        private_key_pem = env.get("SECRET_KEY", "")
        private_key = load_pem_private_key(
            private_key_pem.encode("utf-8"),
            password=None,
            backend=default_backend(),
        )
        return private_key


class MessageVerifier:
    def get_public_keys(self):
        r = get_redis()
        public_keys = {}
        s = requests.Session()
        all_public_keys = PublicKey.objects.filter(is_active=1)
        for current_public_key in all_public_keys:
            redis_jwks_key = str(current_public_key.id) + "-jwks"
            current_kid = current_public_key.key_id
            if r.exists(redis_jwks_key):
                k = r.get(redis_jwks_key)
                key = json.loads(k)
            else:
                response = s.get(current_public_key.url)
                jwks_data = response.json()
                if "keys" in jwks_data:
                    jwk = next(
                        (
                            item
                            for item in jwks_data["keys"]
                            if item["kid"] == current_kid
                        ),
                        None,
                    )
                else:
                    if "kid" in jwks_data.keys():
                        jwk = jwks_data if current_kid == jwks_data["kid"] else None
                    else:
                        jwk = None
                key = jwk if jwk else {"000"}

                r.set(redis_jwks_key, json.dumps(key))
                r.expire(redis_jwks_key, 60000)
            public_keys[current_kid] = key
        return public_keys

    def verify_message(self, request: HttpRequest) -> bool:
        stored_public_keys = self.get_public_keys()
        if bool(not stored_public_keys):
            return False

        r = requests.Request(
            request.method,
            request.build_absolute_uri(),
            json=request.data,
            headers=request.headers,
        )

        for _, json_web_token in stored_public_keys.items():
            verifier = HTTPMessageVerifier(
                signature_algorithm=algorithms.RSA_PSS_SHA512,
                key_resolver=BlenderHTTPSignatureKeyResolver(jwk=json_web_token),
            )
            verifier.verify(r)
        return True


class ResponseSigner:
    def __init__(self):
        self.signing_url = env.get("FLIGHT_PASSPORT_SIGNING_URL", None)
        self.signing_client_id = env.get("FLIGHT_PASSPORT_SIGNING_CLIENT_ID")
        self.signing_client_secret = env.get("FLIGHT_PASSPORT_SIGNING_CLIENT_SECRET")
        self.jose_signing_algorithm = "PS512"

    def generate_content_digest(self, payload):
        payload_str = json.dumps(payload)
        return str(
            http_sfv.Dictionary(
                {"sha-512": hashlib.sha512(payload_str.encode("utf-8")).digest()}
            )
        )

    def sign_json_via_django(self, data_to_sign):
        signer = Signer()
        signed_obj = signer.sign_object(data_to_sign)
        return signed_obj

    def sign_json_via_jose(self, payload):
        """
        For a payload sign using the OIDC private key and return signed JWS
        """

        private_key = env.get("SECRET_KEY", None)
        if private_key:
            try:
                key = jwk.JWK.from_pem(private_key.encode("utf8"))
            except Exception:
                key = None

        if key:
            payload_str = json.dumps(payload)
            jws_token = jws.JWS(payload=payload_str)

            jws_token.add_signature(
                key=key,
                alg=self.jose_signing_algorithm,
                protected=json_encode(
                    {"alg": self.jose_signing_algorithm, "kid": key.thumbprint()}
                ),
            )

            sig = jws_token.serialize()
            s = json.loads(sig)

            signed_response = {
                "signature": s["protected"] + "." + s["payload"] + "." + s["signature"]
            }
            return signed_response
        else:
            return {}

    def sign_http_message_via_ietf(
        self, json_payload, original_request: HttpRequest
    ) -> HttpResponse:
        response = HttpResponse()
        response.url = original_request.build_absolute_uri()
        response.request = original_request
        content_digest = self.generate_content_digest(payload=json_payload)
        response["Content-Digest"] = content_digest
        response["Content-Type"] = "application/json"

        signer = HTTPMessageSigner(
            signature_algorithm=algorithms.RSA_PSS_SHA512,
            key_resolver=BlenderHTTPSignatureKeyResolver(jwk=None),
        )
        signer.sign(
            response,
            key_id="001",  # TODO: Remove hardcoded key_id once e2e test is done
            covered_component_ids=(
                "@method",
                "@authority",
                "@target-uri",
                "content-digest",
            ),
            label="sig1",
        )
        return response
