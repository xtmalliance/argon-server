# API to submit Flight Declarations into Spotlight

from functools import wraps
import json
from __main__ import app
from flask_uuid import FlaskUUID
from six.moves.urllib.request import urlopen
from auth import AuthError, requires_auth, requires_scope
from flask import request, Response

@requires_auth
@app.route("/submit_flight_declaration/", methods=['POST'])
def post_flight_declaration():
    

    try:
        assert request.headers['Content-Type'] == 'application/json'   
    except AssertionError as ae:     
        msg = {"message":"Unsupported Media Type"}
        return Response(json.dumps(msg), status=415, mimetype='application/json')
    else:    
        req = json.loads(request.data)

    try:
        observations = req['observations']   

    except KeyError as ke:
        msg = json.dumps({"message":"One parameter are required: observations with a list of observation objects. One or more of these were not found in your JSON request. For sample data see: https://github.com/openskies-sh/airtraffic-data-protocol-development/blob/master/Airtraffic-Data-Protocol.md#sample-traffic-object"})
        
        return Response(msg, status=400, mimetype='application/json')

    else:
        for observation in observations:  
            lat_dd = observation['lat_dd']
            lon_dd = observation['lon_dd']
            altitude_mm = observation['altitude_mm']
            traffic_source = observation['traffic_source']
            source_type = observation['source_type']
            icao_address = observation['icao_address']
            single_observation = {'lat_dd': lat_dd,'lon_dd':lon_dd,'altitude_mm':altitude_mm, 'traffic_source':traffic_source, 'source_type':source_type, 'icao_address':icao_address }
            task = write_incoming_data.delay(single_observation)  # Send a job to the task queue


    op = json.dumps ({"message":"OK"})
    return Response(op, status=200, mimetype='application/json')
