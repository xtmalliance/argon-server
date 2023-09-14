import json

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from conftest import get_oauth2_token

JWT = get_oauth2_token()


class GeoFencePostTests(APITestCase):
    """
    Contains tests for the function set_geo_fence in views.
    """

    def setUp(self):
        self.client.defaults["HTTP_AUTHORIZATION"] = "Bearer " + JWT
        self.api_url = reverse("set_geo_fence")

    def test_invalid_content_type(self):
        """
        The endpoint expects the content-type in application/json. If anything else is provided an error is thrown.
        """

        response = self.client.post(self.api_url, content_type="text/plain")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_empty_json_payload(self):
        """
        The endpoint expects all fields to be provided. Errors will be thrown otherwise.
        """
        empty_payload = {}
        response = self.client.post(
            self.api_url, content_type="application/json", data=empty_payload
        )
        response_json = {
            "type": ["This field is required."],
            "features": ["This field is required."],
        }
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), response_json)

    def test_incomplete_payload(self):
        """
        The endpoint expects certain fields to be provided. Errors will be thrown otherwise.
        """
        incomplete_payload = {
            "type": "FeatureCollection",
            "features": [{"type": "Feature"}],
        }
        response = self.client.post(
            self.api_url,
            content_type="application/json",
            data=json.dumps(incomplete_payload),
        )
        response_json = {
            "features": {
                "0": {
                    "properties": ["This field is required."],
                    "geometry": ["A valid geometry object must be provided."],
                }
            }
        }
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), response_json)

    def test_invalid_data_types_payload(self):
        """
        The endpoint expects certain fields to be provided. Errors will be thrown otherwise.
        """
        invalid_payload = {
            "type": False,
            "features": [
                {
                    "type": 1,
                    "properties": {
                        "upper_limit": "678",
                        "lower_limit": "100",
                        "start_time": "2023",
                        "end_time": "2024",
                        "name": "Yapa's fence",
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [30.142621994018555, -1.985209815625593],
                                [30.156269073486328, -1.985209815625593],
                                [30.156269073486328, -1.9534712184928378],
                                [30.142621994018555, -1.9534712184928378],
                                [30.142621994018555, -1.985209815625593],
                            ]
                        ],
                    },
                }
            ],
        }
        response = self.client.post(
            self.api_url,
            content_type="application/json",
            data=json.dumps(invalid_payload),
        )
        response_json = {
            "type": ["Not a valid string."],
            "features": {
                "0": {
                    "properties": {
                        "start_time": [
                            "Date has wrong format. Use one of these formats instead: YYYY-MM-DD."
                        ],
                        "end_time": [
                            "Date has wrong format. Use one of these formats instead: YYYY-MM-DD."
                        ],
                    }
                }
            },
        }
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), response_json)

    def test_valid_payload(self):
        """
        The endpoint has valid payload.
        """
        valid_payload = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "upper_limit": "678",
                        "lower_limit": "100",
                        "start_time": "2023-07-20",
                        "end_time": "2023-07-23",
                        "name": "Yapa's fence",
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [30.142621994018555, -1.985209815625593],
                                [30.156269073486328, -1.985209815625593],
                                [30.156269073486328, -1.9534712184928378],
                                [30.142621994018555, -1.9534712184928378],
                                [30.142621994018555, -1.985209815625593],
                            ]
                        ],
                    },
                }
            ],
        }
        response = self.client.post(
            self.api_url,
            content_type="application/json",
            data=json.dumps(valid_payload),
        )
        self.assertEqual(response.json()["message"], "Geofence Declaration submitted")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
