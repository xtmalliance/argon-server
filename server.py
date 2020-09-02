from flask import Flask, url_for
from flask import render_template
from functools import wraps
from flask import request, Response
import requests, json
import logging
from walrus import Database

app = Flask(__name__)

db = Database()
stream = db.Stream('sensor-1')

@app.route("/")
def home():
    return "Flight Blender"

@app.route('/set_air_traffic', methods = ['POST'])
def set_air_traffic():
    
    ''' This is the main POST method that takes in a request for Air traffic observation and processes the input data '''    



    if request.headers['Content-Type'] == 'application/json':
        pass
    else:
    
        msg = {"message":"Unsupported Media Type"}
        return Response(json.dumps(msg), status=415, mimetype='application/json')
    
    req = json.loads(request.data)
    flight_id = req['icao_address']
    try:
        observations = req['observations']   
    except KeyError as e:
        msg = json.dumps({"message":"One parameter are required: observations with a list of observations. One or more of these were not found in your JSON request."})
        return Response(msg, status=400, mimetype='application/json')

    try:
        
        stream = db.Stream(flight_id)

    except KeyError as e:
        msg = json.dumps({"message":"One parameter are required: observations with a list of observations. One or more of these were not found in your JSON request."})
        return Response(msg, status=400, mimetype='application/json')
    else:
        
        msg = json.dumps({"message":"Invalid JSON submitted."})
        return Response(msg, status=400, mimetype='application/json')


    op = json.dumps ({"message":"OK"})
    return Response(op, status=200, mimetype='application/json')

if __name__ == '__main__':
    app.run()