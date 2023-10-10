"""
This file contains unit tests for the views functions in flight_declaration_operations
"""
import datetime
import hashlib
import json
from unittest.mock import patch

import http_sfv
import pytest
import requests
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from django.urls import reverse
from http_message_signatures import (HTTPMessageSigner,
                                     HTTPSignatureKeyResolver, algorithms)
from rest_framework import status
from rest_framework.test import APITestCase

from conftest import get_oauth2_token
from security import helper

JWT = get_oauth2_token()


class _TestHTTPSignatureKeyResolver(HTTPSignatureKeyResolver):
    def resolve_private_key(self, key_id: str):
        with open(f"security/test_keys/{key_id}.key", "rb") as fh:
            return load_pem_private_key(fh.read(), password=None)


class FlightDeclarationPostTests(APITestCase):
    """
    Contains tests for the function set_flight_declaration in views.
    """

    def setUp(self):
        self.client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {JWT}"
        self.api_url = reverse("set_flight_declaration")
        self.flight_time = (
            datetime.datetime.now() + datetime.timedelta(days=1)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.valid_flight_declaration_geo_json = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "id": "0",
                        "start_datetime": "2023-02-03T16:29:08.842Z",
                        "end_datetime": "2023-02-03T16:29:08.842Z",
                        "max_altitude": {"meters": 152.4, "datum": "agl"},
                        "min_altitude": {"meters": 102.4, "datum": "agl"},
                    },
                    "geometry": {
                        "coordinates": [
                            [15.776083042366338, 1.18379149158649],
                            [15.799823306116707, 1.2159036290562142],
                            [15.812391681043636, 1.2675614791659342],
                            [15.822167083764754, 1.3024648511225934],
                            [15.82635654207283, 1.3220105290909174],
                        ],
                        "type": "LineString",
                    },
                }
            ],
        }

    def test_invalid_content_type(self):
        """
        The endpoint expects the content-type in application/json. If anything else is provided an error is thrown.
        """

        response = self.client.post(self.api_url, content_type="text/plain")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_empty_json_payload(self):
        """
        The endpoint expects certain fields to be provided. Errors will be thrown otherwise.
        """
        empty_payload = {}
        response = self.client.post(
            self.api_url, content_type="application/json", data=empty_payload
        )
        response_json = {
            "flight_declaration_geo_json": [
                "A valid flight declaration as specified by the A flight declaration protocol must be submitted."
            ],
        }
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), response_json)

    def test_valid_payload_with_expired_dates(self):
        """
        The payload is valid but start and end dates are expired.
        """
        payload_with_expired_dates = {
            "start_datetime": "2023-01-01T15:00:00+00:00",
            "end_datetime": "2023-01-01T15:00:00+00:00",
            "flight_declaration_geo_json": self.valid_flight_declaration_geo_json,
        }

        response = self.client.post(
            self.api_url,
            content_type="application/json",
            data=json.dumps(payload_with_expired_dates),
        )

        response_json = {
            "message": "A flight declaration cannot have a start or end time in the past or after two days from current time."
        }

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), response_json)

    def test_payload_with_invalid_geometry(self):
        """
        The payload with invalid geometry.
        """
        valid_payload_with_invalid_geometry = {
            "start_datetime": self.flight_time,
            "end_datetime": self.flight_time,
            "flight_declaration_geo_json": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "id": "0",
                            "start_datetime": "2023-02-03T16:29:08.842Z",
                            "end_datetime": "2023-02-03T16:29:08.842Z",
                            "max_altitude": {"meters": 152.4, "datum": "agl"},
                            "min_altitude": {"meters": 102.4, "datum": "agl"},
                        },
                        "geometry": {
                            "coordinates": [
                                [15.776083042366338, 1.18379149158649],
                                [15.776083042366338, 1.18379149158649],
                                [15.776083042366338, 1.18379149158649],
                                [15.776083042366338, 1.18379149158649],
                                [15.776083042366338, 1.18379149158649],
                            ],
                            "type": "LineString",
                        },
                    }
                ],
            },
        }

        response = self.client.post(
            self.api_url,
            content_type="application/json",
            data=json.dumps(valid_payload_with_invalid_geometry),
        )
        response_json = {
            "message": "Error in processing the submitted GeoJSON: every Feature in a GeoJSON FeatureCollection must have a valid geometry, please check your submitted FeatureCollection"
        }
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), response_json)

    def test_payload_with_no_altitudes(self):
        """
        The payload with invalid geometry.
        """
        valid_payload_with_invalid_geometry = {
            "start_datetime": self.flight_time,
            "end_datetime": self.flight_time,
            "flight_declaration_geo_json": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "id": "0",
                            "start_datetime": "2023-02-03T16:29:08.842Z",
                            "end_datetime": "2023-02-03T16:29:08.842Z",
                        },
                        "geometry": {
                            "coordinates": [
                                [15.776083042366338, 1.18379149158649],
                                [15.799823306116707, 1.2159036290562142],
                                [15.812391681043636, 1.2675614791659342],
                                [15.822167083764754, 1.3024648511225934],
                                [15.82635654207283, 1.3220105290909174],
                            ],
                            "type": "LineString",
                        },
                    }
                ],
            },
        }

        response = self.client.post(
            self.api_url,
            content_type="application/json",
            data=json.dumps(valid_payload_with_invalid_geometry),
        )
        response_json = {
            "message": "Error in processing the submitted GeoJSON: every Feature in a GeoJSON FeatureCollection must have a min_altitude and max_altitude data structure"
        }
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), response_json)

    def test_valid_payload(self):
        """
        The payload is valid.
        """
        valid_payload = {
            "start_datetime": self.flight_time,
            "end_datetime": self.flight_time,
            "flight_declaration_geo_json": self.valid_flight_declaration_geo_json,
        }

        response = self.client.post(
            self.api_url,
            content_type="application/json",
            data=json.dumps(valid_payload),
        )
        self.assertEqual(response.json()["message"], "Submitted Flight Declaration")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class FlightDeclarationSignedPostTests(APITestCase):
    """
    Contains tests for the function set_signed_flight_declaration in views.
    """

    def setUp(self):
        self.key_id = "001"
        self.client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {JWT}"
        self.api_url = reverse("set_signed_flight_declaration")

        _flight_time = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        _flight_declaration_geo_json = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "id": "0",
                        "start_datetime": "2023-02-03T16:29:08.842Z",
                        "end_datetime": "2023-02-03T16:29:08.842Z",
                        "max_altitude": {"meters": 152.4, "datum": "agl"},
                        "min_altitude": {"meters": 102.4, "datum": "agl"},
                    },
                    "geometry": {
                        "coordinates": [
                            [15.776083042366338, 1.18379149158649],
                            [15.799823306116707, 1.2159036290562142],
                            [15.812391681043636, 1.2675614791659342],
                            [15.822167083764754, 1.3024648511225934],
                            [15.82635654207283, 1.3220105290909174],
                        ],
                        "type": "LineString",
                    },
                }
            ],
        }

        _payload = {
            "start_datetime": _flight_time,
            "end_datetime": _flight_time,
            "flight_declaration_geo_json": _flight_declaration_geo_json,
        }

        _request = requests.Request(
            "POST",
            "http://testserver/flight_declaration_ops/set_signed_flight_declaration",  # testserver is the @authority for pytest HTTP requests
            json=_payload,
        )
        self.http_request = _request
        self.valid_payload = _payload

    def test_unsupported_media_type(self):
        response = self.client.post(
            self.api_url, content_type="text/plain", data="TEXT PAYLOAD"
        )

        self.assertEqual(response.json(), {"message": "Unsupported Media Type"})
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_invalid_signed_request(self):
        response = self.client.post(
            self.api_url,
            content_type="application/json",
            data=json.dumps(self.valid_payload),
        )

        self.assertEqual(
            response.json()["message"],
            "Could not verify against public keys of USSP client(GCS) setup in Flight Blender",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("security.signing.MessageVerifier.get_public_keys")
    def test_valid_signed_request_but_incorrect_payload(self, mock_get_public_keys):
        invalid_payload = {
            "start_datetime": "2023-09-20T13:00:00.000",
            "end_datetime": "2023-09-20T13:00:00.000",
            "flight_declaration_geo_json": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "id": "0",
                            "start_datetime": "2023-02-03T16:29:08.842Z",
                            "end_datetime": "2023-02-03T16:29:08.842Z",
                            "max_altitude": {"meters": 152.4, "datum": "agl"},
                            "min_altitude": {"meters": 102.4, "datum": "agl"},
                        },
                        "geometry": {
                            "coordinates": [
                                [15.776083042366338, 1.18379149158649],
                                [15.799823306116707, 1.2159036290562142],
                                [15.812391681043636, 1.2675614791659342],
                                [15.822167083764754, 1.3024648511225934],
                                [15.82635654207283, 1.3220105290909174],
                            ],
                            "type": "LineString",
                        },
                    }
                ],
            },
        }
        # Sign the http request: This mocks the ussp_link's http request signing part.
        data = json.dumps(invalid_payload, separators=(",", ":"))
        content_digest = str(
            http_sfv.Dictionary({"sha-512": hashlib.sha512(data.encode()).digest()})
        )
        request = self.http_request.prepare()
        request.body = invalid_payload
        request.headers["Content-Digest"] = content_digest
        signer = HTTPMessageSigner(
            signature_algorithm=algorithms.RSA_PSS_SHA512,
            key_resolver=_TestHTTPSignatureKeyResolver(),
        )
        signer.sign(
            request,
            key_id=self.key_id,
            covered_component_ids=(
                "@method",
                "@authority",
                "@target-uri",
                "content-digest",
            ),
            label="sig1",
        )
        assert request.headers.get("Content-Digest")
        assert request.headers.get("Signature-Input")
        assert request.headers.get("Signature")

        headers = {
            "HTTP_Content-Digest": request.headers.get("Content-Digest"),
            "HTTP_Signature-Input": request.headers.get("Signature-Input"),
            "HTTP_Signature": request.headers.get("Signature"),
        }

        # Mock public JWK retrieval
        jwk = helper.get_jwk_from_public_pem_key(
            path=f"/app/security/test_keys/{self.key_id}.pem"
        )
        mock_get_public_keys.return_value = {self.key_id: jwk}

        response = self.client.post(
            self.api_url,
            content_type="application/json",
            data=json.dumps(invalid_payload),
            **headers,
        )

        self.assertEqual(
            response.json()["message"],
            "A flight declaration cannot have a start or end time in the past or after two days from current time.",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("security.signing.MessageVerifier.get_public_keys")
    def test_valid_signed_request(self, mock_get_public_keys):
        # Sign the http request: This mocks the ussp_link's http request signing part.
        data = json.dumps(self.valid_payload, separators=(",", ":"))
        content_digest = str(
            http_sfv.Dictionary({"sha-512": hashlib.sha512(data.encode()).digest()})
        )
        request = self.http_request.prepare()
        request.headers["Content-Digest"] = content_digest
        signer = HTTPMessageSigner(
            signature_algorithm=algorithms.RSA_PSS_SHA512,
            key_resolver=_TestHTTPSignatureKeyResolver(),
        )
        signer.sign(
            request,
            key_id=self.key_id,
            covered_component_ids=(
                "@method",
                "@authority",
                "@target-uri",
                "content-digest",
            ),
            label="sig1",
        )
        assert request.headers.get("Content-Digest")
        assert request.headers.get("Signature-Input")
        assert request.headers.get("Signature")

        headers = {
            "HTTP_Content-Digest": request.headers.get("Content-Digest"),
            "HTTP_Signature-Input": request.headers.get("Signature-Input"),
            "HTTP_Signature": request.headers.get("Signature"),
        }

        # Mock public JWK retrieval
        jwk = helper.get_jwk_from_public_pem_key(
            path=f"/app/security/test_keys/{self.key_id}.pem"
        )
        mock_get_public_keys.return_value = {self.key_id: jwk}

        response = self.client.post(
            self.api_url,
            content_type="application/json",
            data=json.dumps(self.valid_payload),
            **headers,
        )

        self.assertEqual(response.json()["message"], "Submitted Flight Declaration")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Signed response should also have below headers
        assert response.headers.get("Content-Digest")
        assert response.headers.get("Signature-Input")
        assert response.headers.get("Signature")


@pytest.mark.usefixtures("create_flight_plan")
class FlightDeclarationGetTests(APITestCase):
    """
    Contains tests for class FlightDeclarationList
    """

    def setUp(self):
        self.client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {JWT}"
        self.api_url = reverse("flight_declaration")

    def test_count_flight_plans_with_default_filter(self):
        response = self.client.get(
            self.api_url,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["total"], 0)

    def test_count_flight_plans_with_altitude_filter_1(self):
        flight_s_time = "2023-08-01 00:00:00"
        flight_e_time = "2023-08-01 23:00:00"
        response = self.client.get(
            self.api_url
            + "?min_alt=90"
            + "&start_date={flight_s_time}&end_date={flight_e_time}".format(
                flight_s_time=flight_s_time, flight_e_time=flight_e_time
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["total"], 1)

    def test_count_flight_plans_with_altitude_filter_2(self):
        flight_s_time = "2023-08-01 00:00:00"
        flight_e_time = "2023-08-01 23:00:00"
        response = self.client.get(
            self.api_url
            + "?max_alt=100"
            + "&start_date={flight_s_time}&end_date={flight_e_time}".format(
                flight_s_time=flight_s_time, flight_e_time=flight_e_time
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["total"], 2)

    def test_count_flight_plans_with_altitude_filter_3(self):
        flight_s_time = "2023-08-01 00:00:00"
        flight_e_time = "2023-08-01 23:00:00"
        response = self.client.get(
            self.api_url
            + "?max_alt=100&min_alt=90"
            + "&start_date={flight_s_time}&end_date={flight_e_time}".format(
                flight_s_time=flight_s_time, flight_e_time=flight_e_time
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["total"], 1)

    def test_count_flight_plans_with_datetime_filter_1(self):
        flight_s_time = "2023-08-01 06:00:00"
        flight_e_time = "2023-08-01 23:00:00"
        response = self.client.get(
            self.api_url
            + "?start_date={flight_s_time}&end_date={flight_e_time}".format(
                flight_s_time=flight_s_time, flight_e_time=flight_e_time
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["total"], 3)

    def test_count_flight_plans_with_datetime_filter_2(self):
        flight_s_time = "2023-08-01 09:30:00"
        flight_e_time = "2023-08-01 12:30:00"
        response = self.client.get(
            self.api_url
            + "?start_date={flight_s_time}&end_date={flight_e_time}".format(
                flight_s_time=flight_s_time, flight_e_time=flight_e_time
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["total"], 2)

    def test_count_flight_plans_with_datetime_filter_3(self):
        flight_s_time = "2023-08-01 15:30:00"
        flight_e_time = "2023-08-01 17:00:00"
        response = self.client.get(
            self.api_url
            + "?start_date={flight_s_time}&end_date={flight_e_time}".format(
                flight_s_time=flight_s_time, flight_e_time=flight_e_time
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["total"], 1)

    def test_count_flight_plans_with_state_filter_1(self):
        flight_s_time = "2023-08-01 00:00:00"
        flight_e_time = "2023-08-01 23:00:00"
        response = self.client.get(
            self.api_url
            + "?states=1,2,3,4,5"
            + "&start_date={flight_s_time}&end_date={flight_e_time}".format(
                flight_s_time=flight_s_time, flight_e_time=flight_e_time
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["total"], 3)

    def test_count_flight_plans_with_state_filter_2(self):
        flight_s_time = "2023-08-01 00:00:00"
        flight_e_time = "2023-08-01 23:00:00"
        response = self.client.get(
            self.api_url
            + "?states=2,3"
            + "&start_date={flight_s_time}&end_date={flight_e_time}".format(
                flight_s_time=flight_s_time, flight_e_time=flight_e_time
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["total"], 2)

    def test_count_flight_plans_with_state_filter_3(self):
        flight_s_time = "2023-08-01 00:00:00"
        flight_e_time = "2023-08-01 23:00:00"
        response = self.client.get(
            self.api_url
            + "?states=3"
            + "&start_date={flight_s_time}&end_date={flight_e_time}".format(
                flight_s_time=flight_s_time, flight_e_time=flight_e_time
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["total"], 1)

    def test_count_flight_plans_with_state_filter_4(self):
        flight_s_time = "2023-08-01 00:00:00"
        flight_e_time = "2023-08-01 23:00:00"
        response = self.client.get(
            self.api_url
            + "?states=4,5"
            + "&start_date={flight_s_time}&end_date={flight_e_time}".format(
                flight_s_time=flight_s_time, flight_e_time=flight_e_time
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["total"], 0)

    def test_count_flight_plans_with_aircraft_ids(self):
        flight_s_time = "2023-08-01 00:00:00"
        flight_e_time = "2023-08-01 23:00:00"
        response = self.client.get(
            self.api_url
            + "?start_date={flight_s_time}&end_date={flight_e_time}".format(
                flight_s_time=flight_s_time, flight_e_time=flight_e_time
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["total"], 3)

        self.assertEqual(response.json()["results"][0]["aircraft_id"], "334455")
        self.assertEqual(response.json()["results"][1]["aircraft_id"], "000")
        self.assertEqual(response.json()["results"][2]["aircraft_id"], "112233")
