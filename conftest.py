import json
from os import environ as env

import pytest
import requests
from rest_framework import status

from flight_declaration_operations import models as fdo_models
from flight_feed_operations import models as ffo_models
from non_repudiation import models as nr_models


def get_oauth2_token():
    # Request a new OAuth2 token
    data = {
        "grant_type": "client_credentials",
        "client_id": env.get("CLIENT_ID", ""),
        "client_secret": env.get("CLIENT_SECRET", ""),
        "scope": "blender.write blender.read",
        "audience": env.get("PASSPORT_AUDIENCE", ""),
    }
    token_url = env.get("PASSPORT_URL", "") + env.get("PASSPORT_TOKEN_URL", "")
    response = requests.post(token_url, data=data)

    # Check for a successful response and return the token
    if response.status_code == status.HTTP_200_OK:
        token_data = response.json()
        return token_data.get("access_token")
    else:
        raise ValueError(
            f"Failed to obtain OAuth2 token. Status code: {response.status_code}"
        )


@pytest.fixture(scope="function")
def mock_env_passport_url():
    # Set the environment variable PASSPORT_URL to the mocked value
    original_passport_url = env.get("PASSPORT_URL", "")
    env["PASSPORT_URL"] = "https://invalid_passporturl.com"

    # Yield control back to the test
    yield

    # Restore the environment variable: PASSPORT_URL to its original value
    env["PASSPORT_URL"] = original_passport_url


@pytest.fixture(scope="function")
def mock_env_secret_key():
    # Set the environment variable SECRET_KEY to the mocked value
    original_secret_key = env.get("SECRET_KEY", "")

    with open("security/test_keys/001.key", "r") as key_file:
        private_key = key_file.read()
    env["SECRET_KEY"] = private_key

    # Yield control back to the test
    yield

    # Restore the environment variable: PASSPORT_URL to its original value
    env["SECRET_KEY"] = original_secret_key


@pytest.mark.django_db
@pytest.fixture(scope="function")
def create_flight_plan(db) -> None:
    # Flight plan 1
    max_alt = 100
    min_alt = 90
    flight_s_time = "2023-08-01T9:00:00+00:00"
    flight_e_time = "2023-08-01T10:00:00+00:00"
    fdo_models.FlightDeclaration.objects.create(
        operational_intent={
            "volumes": [
                {
                    "volume": {
                        "outline_polygon": {
                            "vertices": [
                                {
                                    "lat": 3.0000070710678117,
                                    "lng": 1.999992928932188,
                                },
                                {
                                    "lat": 3.000007730104534,
                                    "lng": 1.9999936560671583,
                                },
                                {
                                    "lat": 2.0000070710678117,
                                    "lng": 0.9999929289321882,
                                },
                            ]
                        },
                        "altitude_lower": {
                            "value": min_alt,
                            "reference": "W84",
                            "units": "M",
                        },
                        "altitude_upper": {
                            "value": max_alt,
                            "reference": "W84",
                            "units": "M",
                        },
                        "outline_circle": None,
                    },
                    "time_start": {
                        "format": "RFC3339",
                        "value": "2023-07-26T15:00:00+00:00",
                    },
                    "time_end": {
                        "format": "RFC3339",
                        "value": "2023-07-26T16:00:00+00:00",
                    },
                }
            ],
            "priority": 0,
            "state": "Accepted",
            "off_nominal_volumes": [],
        },
        bounds="",
        type_of_operation=1,
        submitted_by="User 001",
        is_approved=False,
        state=1,
        start_datetime=flight_s_time,
        end_datetime=flight_e_time,
        originating_party="Party 001",
        flight_declaration_raw_geojson=json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "id": "0",
                            "start_datetime": "2023-08-10T16:29:08.842Z",
                            "end_datetime": "2023-08-10T19:29:08.842Z",
                            "max_altitude": {"meters": max_alt, "datum": "agl"},
                            "min_altitude": {"meters": min_alt, "datum": "agl"},
                        },
                        "geometry": {
                            "coordinates": [[1, 2], [2, 3]],
                            "type": "LineString",
                        },
                    }
                ],
            }
        ),
    )
    # Flight plan 2

    max_alt = 120
    min_alt = 70
    flight_s_time = "2023-08-01T11:00:00+00:00"
    flight_e_time = "2023-08-01T12:00:00+00:00"
    fdo_models.FlightDeclaration.objects.create(
        operational_intent={
            "volumes": [
                {
                    "volume": {
                        "outline_polygon": {
                            "vertices": [
                                {
                                    "lat": 3.0000070710678117,
                                    "lng": 1.999992928932188,
                                },
                                {
                                    "lat": 3.000007730104534,
                                    "lng": 1.9999936560671583,
                                },
                                {
                                    "lat": 2.0000070710678117,
                                    "lng": 0.9999929289321882,
                                },
                            ]
                        },
                        "altitude_lower": {
                            "value": min_alt,
                            "reference": "W84",
                            "units": "M",
                        },
                        "altitude_upper": {
                            "value": max_alt,
                            "reference": "W84",
                            "units": "M",
                        },
                        "outline_circle": None,
                    },
                    "time_start": {
                        "format": "RFC3339",
                        "value": "2023-07-26T15:00:00+00:00",
                    },
                    "time_end": {
                        "format": "RFC3339",
                        "value": "2023-07-26T16:00:00+00:00",
                    },
                }
            ],
            "priority": 0,
            "state": "Accepted",
            "off_nominal_volumes": [],
        },
        bounds="",
        type_of_operation=1,
        submitted_by="User 002",
        is_approved=False,
        state=2,
        start_datetime=flight_s_time,
        end_datetime=flight_e_time,
        originating_party="Party 002",
        flight_declaration_raw_geojson=json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "id": "0",
                            "start_datetime": "2023-08-10T16:29:08.842Z",
                            "end_datetime": "2023-08-10T19:29:08.842Z",
                            "max_altitude": {"meters": max_alt, "datum": "agl"},
                            "min_altitude": {"meters": min_alt, "datum": "agl"},
                        },
                        "geometry": {
                            "coordinates": [[1, 2], [2, 3]],
                            "type": "LineString",
                        },
                    }
                ],
            }
        ),
    )
    # Flight plan 2
    max_alt = 100
    min_alt = 80
    flight_s_time = "2023-08-01T15:00:00+00:00"
    flight_e_time = "2023-08-01T16:00:00+00:00"
    fdo_models.FlightDeclaration.objects.create(
        operational_intent={
            "volumes": [
                {
                    "volume": {
                        "outline_polygon": {
                            "vertices": [
                                {
                                    "lat": 3.0000070710678117,
                                    "lng": 1.999992928932188,
                                },
                                {
                                    "lat": 3.000007730104534,
                                    "lng": 1.9999936560671583,
                                },
                                {
                                    "lat": 2.0000070710678117,
                                    "lng": 0.9999929289321882,
                                },
                            ]
                        },
                        "altitude_lower": {
                            "value": min_alt,
                            "reference": "W84",
                            "units": "M",
                        },
                        "altitude_upper": {
                            "value": max_alt,
                            "reference": "W84",
                            "units": "M",
                        },
                        "outline_circle": None,
                    },
                    "time_start": {
                        "format": "RFC3339",
                        "value": "2023-07-26T15:00:00+00:00",
                    },
                    "time_end": {
                        "format": "RFC3339",
                        "value": "2023-07-26T16:00:00+00:00",
                    },
                }
            ],
            "priority": 0,
            "state": "Accepted",
            "off_nominal_volumes": [],
        },
        bounds="",
        type_of_operation=1,
        submitted_by="User 003",
        is_approved=False,
        state=3,
        start_datetime=flight_s_time,
        end_datetime=flight_e_time,
        originating_party="Party 003",
        flight_declaration_raw_geojson=json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "id": "0",
                            "start_datetime": "2023-08-10T16:29:08.842Z",
                            "end_datetime": "2023-08-10T19:29:08.842Z",
                            "max_altitude": {"meters": max_alt, "datum": "agl"},
                            "min_altitude": {"meters": min_alt, "datum": "agl"},
                        },
                        "geometry": {
                            "coordinates": [[1, 2], [2, 3]],
                            "type": "LineString",
                        },
                    }
                ],
            }
        ),
    )
    yield
    fdo_models.FlightDeclaration.objects.all().delete()


@pytest.mark.django_db
@pytest.fixture(scope="function")
def create_public_keys(db) -> None:
    nr_models.PublicKey.objects.create(
        key_id="001", url="http://publickeyTrue.com", is_active=True
    )

    nr_models.PublicKey.objects.create(
        key_id="002", url="http://publickeyFalse.com", is_active=False
    )

    nr_models.PublicKey.objects.create(
        key_id="003", url="http://publickey.com", is_active=True
    )
    yield
    nr_models.PublicKey.objects.all().delete()
