from flask import Flask, url_for
from flask import render_template
from functools import wraps
from flask import request, Response
import requests, json
from datetime import datetime
import logging
import redis
from walrus import Database
from datetime import datetime, timedelta
import time
from celery import Celery
import celeryconfig
import os
from flask import jsonify

from auth import AuthError, requires_auth
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from flight_declaration_writer import fd_blueprint
from gen_fence_writer import gf_blueprint
from rid_dss_operations import dss_rid_blueprint

app = Flask(__name__)
app.config.from_object('config')

# register other endpoints
app.register(fd_blueprint)
app.register(gf_blueprint)
app.register(dss_rid_blueprint)




@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response

def make_celery(app):
    # create context tasks in celery
    celery = Celery(
        app.import_name,
        broker=app.config['BROKER_URL']
    )
    celery.conf.update(app.config)
    celery.config_from_object(celeryconfig)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask

    return celery

celery = make_celery(app)



def get_consumer_group(create=False):
    db = Database(host=app.config['REDIS_HOST'], port =app.config['REDIS_PORT'])   
    stream_keys = ['all_observations']
    
    cg = db.time_series('cg-obs', stream_keys)
    if create:
        for stream in stream_keys:
            db.xadd(stream, {'data': ''})

    if create:
        cg.create()
        cg.set_id('$')

    return cg.all_observations

get_consumer_group(create=True)

@celery.task()
def write_incoming_data(observation): 
    cg = get_consumer_group()           
    msgid =cg.add(observation)    
        
    return msgid



@app.route("/")
def home():
    return "Flight Blender"

@app.route('/set_air_traffic', methods = ['POST'])
def set_air_traffic():
    
    ''' This is the main POST method that takes in a request for Air traffic observation and processes the input data '''  


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



if __name__ == '__main__':
    app.run(port=8080)