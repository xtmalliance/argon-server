import hashlib
import json
from unittest.mock import patch

import http_sfv
import requests
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from django.test import TestCase
from http_message_signatures import (
    HTTPMessageSigner,
    HTTPSignatureKeyResolver,
    algorithms,
)

import security.helper as helper
from security.signing import MessageVerifier


class _MyHTTPSignatureKeyResolver(HTTPSignatureKeyResolver):
    def resolve_private_key(self, key_id: str):
        with open(f"security/test_keys/{key_id}.key", "rb") as fh:
            return load_pem_private_key(fh.read(), password=None)


class MessageVerifierTests(TestCase):
    def setUp(self):
        # Create a request with payload
        self.key_id = "001"
        _payload = {"type_of_operation": 1, "originating_party": "TII"}
        _request = requests.Request(
            "POST",
            "http://localhost:8000/flight_declaration_ops/set_signed_flight_declaration",
            json=_payload,
        )

        _data = json.dumps(_payload, separators=(",", ":"))
        _content_digest = str(
            http_sfv.Dictionary({"sha-512": hashlib.sha512(_data.encode()).digest()})
        )

        # Sign the payload with RSA_PSS_SHA512 private key
        self.request = _request.prepare()
        self.request.headers["Content-Digest"] = _content_digest

        _signer = HTTPMessageSigner(
            signature_algorithm=algorithms.RSA_PSS_SHA512,
            key_resolver=_MyHTTPSignatureKeyResolver(),
        )
        _signer.sign(
            self.request,
            key_id=self.key_id,
            covered_component_ids=(
                "@method",
                "@authority",
                "@target-uri",
                "content-digest",
            ),
            label="sig1",
        )

    def test_check_signed_message_content(self):
        """
        Test whether the signed request has propper headers
        """
        assert self.request.headers.get("Content-Digest")
        assert self.request.headers.get("Signature-Input")
        assert self.request.headers.get("Signature")

    @patch("security.signing.MessageVerifier.get_public_keys")
    def test_verify_signed_message(self, mock_get_public_keys):
        """
        Test whether the signed request can be verified using the jwk of the public key
        """
        jwk = helper.get_jwk_from_public_pem_key(
            path=f"/app/security/test_keys/{self.key_id}.pem"
        )
        mock_get_public_keys.return_value = {self.key_id: jwk}

        django_request = helper.http_request_to_django_request(self.request)

        verifier = MessageVerifier()
        is_verified = verifier.verify_message(django_request)

        assert is_verified
