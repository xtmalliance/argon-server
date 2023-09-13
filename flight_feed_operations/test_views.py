"""
This file contains unit tests for the views functions in flight_feed_operations
"""
import datetime
import json

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

JWT = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJ0ZXN0ZmxpZ2h0LmZsaWdodGJsZW5kZXIuY29tIiwiY2xpZW50X2lkIjoidXNzX25vYXV0aCIsImV4cCI6MTY4Nzc4Mjk0OCwiaXNzIjoiTm9BdXRoIiwianRpIjoiODI0OWI5ODgtZjlkZi00YmNhLWI2YTctODVhZGFiZjFhMTUwIiwibmJmIjoxNjg3Nzc5MzQ3LCJzY29wZSI6ImJsZW5kZXIucmVhZCIsInN1YiI6InVzc19ub2F1dGgifQ.b63qZWs08Cp1cgfRCtbQfLom6QQyFpqUaFDNZ9ZdAjSM690StACij6FiriSFhOfFiRBv9rE0DePJzElUSwv1r1bI0IpKMtEJYsJY4DXy7ZImiJ3rSten1nnb1LLAELcDIxMZM2D1ek43EFW35al4si640JfMcSmt62bEP1b4Msc"


class TelemetryPostTests(APITestCase):
    """
    Contains tests for the function set_telemetry in views.
    """

    def setUp(self):
        self.client.defaults["HTTP_AUTHORIZATION"] = "Bearer " + JWT
        self.api_url = reverse("set_telemetry")

    def test_empty_payload(self):
        empty_payload = {}
        response = self.client.put(
            self.api_url, content_type="application/json", data=empty_payload
        )
        response_json = {
            "observations": [
                "A flight observation array with current states and flight details is necessary"
            ]
        }
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), response_json)

    def test_valid_payload(self):
        payload = {
            "observations": [
                {
                    "current_states": [
                        {
                            "timestamp": {
                                "value": "1985-04-12T23:20:50.52Z",
                                "format": "RFC3339",
                            },
                            "timestamp_accuracy": 0,
                            "operational_status": "Undeclared",
                            "position": {
                                "lat": 34.12,
                                "lng": -118.456,
                                "alt": 1321.2,
                                "accuracy_h": "HAUnknown",
                                "accuracy_v": "VAUnknown",
                                "extrapolated": True,
                                "pressure_altitude": 0,
                            },
                            "track": 0,
                            "speed": 1.9,
                            "speed_accuracy": "SAUnknown",
                            "vertical_speed": 0.2,
                            "height": {"distance": 0, "reference": "TakeoffLocation"},
                            "group_radius": 0,
                            "group_ceiling": 0,
                            "group_floor": 0,
                            "group_count": 1,
                            "group_time_start": "2019-08-24T14:15:22Z",
                            "group_time_end": "2019-08-24T14:15:22Z",
                        }
                    ],
                    "flight_details": {
                        "rid_details": {
                            "id": "a3423b-213401-0023",
                            "operator_id": "N.OP123456",
                            "operation_description": "SafeFlightDrone company doing survey with DJI Inspire 2. See my privacy policy www.example.com/privacy.",
                        },
                        "eu_classification": {
                            "category": "EUCategoryUndefined",
                            "class": "EUClassUndefined",
                        },
                        "uas_id": {
                            "serial_number": "INTCJ123-4567-890",
                            "registration_id": "N.123456",
                            "utm_id": "ae1fa066-6d68-4018-8274-af867966978e",
                            "specific_session_id": "02-a1b2c3d4e5f60708",
                        },
                        "operator_location": {
                            "position": {
                                "lng": -118.456,
                                "lat": 34.12,
                                "accuracy_h": "HAUnknown",
                                "accuracy_v": "VAUnknown",
                            },
                            "altitude": 19.5,
                            "altitude_type": "Takeoff",
                        },
                        "auth_data": {"format": "string", "data": 34},
                        "serial_number": "INTCJ123-4567-890",
                        "registration_number": "FA12345897",
                    },
                }
            ]
        }
        response = self.client.put(
            self.api_url, content_type="application/json", data=json.dumps(payload)
        )
        response_json = {"message": "Telemetry data successfully submitted"}
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json(), response_json)

    def test_invalid_current_states_payload(self):
        payload = {
            "observations": [
                {
                    "current_states": [{}],
                    "flight_details": {
                        "rid_details": {
                            "id": "a3423b-213401-0023",
                            "operator_id": "N.OP123456",
                            "operation_description": "SafeFlightDrone company doing survey with DJI Inspire 2. See my privacy policy www.example.com/privacy.",
                        },
                        "eu_classification": {
                            "category": "EUCategoryUndefined",
                            "class": "EUClassUndefined",
                        },
                        "uas_id": {
                            "serial_number": "INTCJ123-4567-890",
                            "registration_id": "N.123456",
                            "utm_id": "ae1fa066-6d68-4018-8274-af867966978e",
                            "specific_session_id": "02-a1b2c3d4e5f60708",
                        },
                        "operator_location": {
                            "position": {
                                "lng": -118.456,
                                "lat": 34.12,
                                "accuracy_h": "HAUnknown",
                                "accuracy_v": "VAUnknown",
                            },
                            "altitude": 19.5,
                            "altitude_type": "Takeoff",
                        },
                        "auth_data": {"format": "string", "data": 34},
                        "serial_number": "INTCJ123-4567-890",
                        "registration_number": "FA12345897",
                    },
                }
            ]
        }
        response = self.client.put(
            self.api_url, content_type="application/json", data=json.dumps(payload)
        )
        response_json = {
            "observations": [
                {
                    "current_states": [
                        {
                            "timestamp": ["This field is required."],
                            "timestamp_accuracy": ["This field is required."],
                            "operational_status": ["This field is required."],
                            "position": ["This field is required."],
                            "track": ["This field is required."],
                            "speed": ["This field is required."],
                            "speed_accuracy": ["This field is required."],
                            "vertical_speed": ["This field is required."],
                            "height": ["This field is required."],
                        }
                    ]
                }
            ]
        }
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), response_json)

    def test_invalid_flight_details_payload(self):
        payload = {
            "observations": [
                {
                    "current_states": [
                        {
                            "timestamp": {
                                "value": "1985-04-12T23:20:50.52Z",
                                "format": "RFC3339",
                            },
                            "timestamp_accuracy": 0,
                            "operational_status": "Undeclared",
                            "position": {
                                "lat": 34.12,
                                "lng": -118.456,
                                "alt": 1321.2,
                                "accuracy_h": "HAUnknown",
                                "accuracy_v": "VAUnknown",
                                "extrapolated": True,
                                "pressure_altitude": 0,
                            },
                            "track": 0,
                            "speed": 1.9,
                            "speed_accuracy": "SAUnknown",
                            "vertical_speed": 0.2,
                            "height": {"distance": 0, "reference": "TakeoffLocation"},
                            "group_radius": 0,
                            "group_ceiling": 0,
                            "group_floor": 0,
                            "group_count": 1,
                            "group_time_start": "2019-08-24T14:15:22Z",
                            "group_time_end": "2019-08-24T14:15:22Z",
                        }
                    ],
                    "flight_details": {},
                }
            ]
        }
        response = self.client.put(
            self.api_url, content_type="application/json", data=json.dumps(payload)
        )
        response_json = {
            "observations": [
                {
                    "flight_details": {
                        "rid_details": ["This field is required."],
                        "eu_classification": ["This field is required."],
                        "uas_id": ["This field is required."],
                        "operator_location": ["This field is required."],
                        "auth_data": ["This field is required."],
                        "serial_number": ["This field is required."],
                        "registration_number": ["This field is required."],
                    }
                }
            ]
        }
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), response_json)
