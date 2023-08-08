
import json

import pytest

from flight_declaration_operations import models as fdo_models


@pytest.mark.django_db
@pytest.fixture(scope="function")
def create_flight_plan(db) -> None:

    # Flight plan 1
    max_alt = 100
    min_alt = 90
    flight_s_time ="2023-08-01T9:00:00+00:00"
    flight_e_time="2023-08-01T10:00:00+00:00"
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
    flight_s_time ="2023-08-01T11:00:00+00:00"
    flight_e_time="2023-08-01T12:00:00+00:00"
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
    flight_s_time ="2023-08-01T15:00:00+00:00"
    flight_e_time="2023-08-01T16:00:00+00:00"
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
