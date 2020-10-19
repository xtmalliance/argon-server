## A module to read data from a DSS instance

from functools import wraps
import json
from __main__ import app
from flask_uuid import FlaskUUID
from six.moves.urllib.request import urlopen
from auth import AuthError, requires_auth, requires_scope


@requires_auth
@app.route("/get_identification_service_areas/<uuid:id>", methods=['GET'], defaults={"id": "00000000-0000-0000-0000-000000000000"})
def get_isa(id):
    return 'it works!'


@requires_auth
@app.route("/get_subscriptions/<uuid:id>", defaults={"id": "00000000-0000-0000-0000-000000000000"},methods=['GET'])
def get_subscriptions(id):
    return 'it works!'


@requires_auth
@app.route("/get_flights", methods=['GET'])
def get_flights(id):
    return 'it works!'


@requires_auth
@app.route("/get_flights/<uuid:id>/details",defaults={"id": "00000000-0000-0000-0000-000000000000"}, methods=['GET'])
def get_flight_id_details(id):
    return 'it works!'

