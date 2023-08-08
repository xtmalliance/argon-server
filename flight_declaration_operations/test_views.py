"""
This file contains unit tests for the views functions in flight_declaration_operations
"""
import datetime
import json

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

JWT = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJ0ZXN0ZmxpZ2h0LmZsaWdodGJsZW5kZXIuY29tIiwiY2xpZW50X2lkIjoidXNzX25vYXV0aCIsImV4cCI6MTY4Nzc4Mjk0OCwiaXNzIjoiTm9BdXRoIiwianRpIjoiODI0OWI5ODgtZjlkZi00YmNhLWI2YTctODVhZGFiZjFhMTUwIiwibmJmIjoxNjg3Nzc5MzQ3LCJzY29wZSI6ImJsZW5kZXIucmVhZCIsInN1YiI6InVzc19ub2F1dGgifQ.b63qZWs08Cp1cgfRCtbQfLom6QQyFpqUaFDNZ9ZdAjSM690StACij6FiriSFhOfFiRBv9rE0DePJzElUSwv1r1bI0IpKMtEJYsJY4DXy7ZImiJ3rSten1nnb1LLAELcDIxMZM2D1ek43EFW35al4si640JfMcSmt62bEP1b4Msc"


class FlightDeclarationPostTests(APITestCase):
    """
    Contains tests for the function set_flight_declaration in views.
    """

    def setUp(self):
        self.client.defaults["HTTP_AUTHORIZATION"] = "Bearer " + JWT
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
        self.assertEqual(response.status_code, status.HTTP_200_OK)


@pytest.mark.usefixtures("create_flight_plan")
class FlightDeclarationGetTests(APITestCase):
    """
    Contains tests for class FlightDeclarationList
    """

    def setUp(self):
        self.client.defaults["HTTP_AUTHORIZATION"] = "Bearer " + JWT
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
