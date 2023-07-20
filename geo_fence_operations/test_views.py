import json
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

JWT = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJ0ZXN0ZmxpZ2h0LmZsaWdodGJsZW5kZXIuY29tIiwiY2xpZW50X2lkIjoidXNzX25vYXV0aCIsImV4cCI6MTY4Nzc4Mjk0OCwiaXNzIjoiTm9BdXRoIiwianRpIjoiODI0OWI5ODgtZjlkZi00YmNhLWI2YTctODVhZGFiZjFhMTUwIiwibmJmIjoxNjg3Nzc5MzQ3LCJzY29wZSI6ImJsZW5kZXIucmVhZCIsInN1YiI6InVzc19ub2F1dGgifQ.b63qZWs08Cp1cgfRCtbQfLom6QQyFpqUaFDNZ9ZdAjSM690StACij6FiriSFhOfFiRBv9rE0DePJzElUSwv1r1bI0IpKMtEJYsJY4DXy7ZImiJ3rSten1nnb1LLAELcDIxMZM2D1ek43EFW35al4si640JfMcSmt62bEP1b4Msc"


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
