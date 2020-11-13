from flask import Flask, url_for, current_app
from flask import render_template
from flask import request, Response
from flask import jsonify

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from functools import wraps
import requests, json, redis, os, time
from datetime import datetime
from walrus import Database
from datetime import datetime, timedelta
from celery import Celery
import celeryconfig
from shapely.geometry import box
from auth import AuthError, requires_auth, requires_authority_auth, requires_scope
from flask_logs import LogSetup
from flight_declaration_ops import flight_declaration_writer
from geo_fence_ops import geo_fence_writer
from dss_ops import rid_dss_operations

app = Flask(__name__)
app.config.from_object('config')
app.config["LOG_TYPE"] = os.getenv("LOG_TYPE", "stream")
app.config["LOG_LEVEL"] = os.getenv("LOG_LEVEL", "INFO")

logs = LogSetup()
logs.init_app(app)

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

# create a consumer group once
get_consumer_group(create=True)

# TODO: Build Flask Blueprints, move the celery calls to their modules. 

#### Airtraffic Endpoint
@celery.task()
def write_incoming_data(observation): 
    cg = get_consumer_group()           
    msgid = cg.add(observation)            
    return msgid

@requires_auth
@requires_scope('blender.write')
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

#### Flight Declaration Module / Endpoint

@celery.task()
def write_flight_declaration(fd):   
    my_credential_ops = flight_declaration_writer.PassportCredentialsGetter()        
    fd_credentials = my_credential_ops.get_cached_credentials()
    try: 
        assert any(fd_credentials) == True # Dictionary is populated 
    except AssertionError as e: 
        # Error in Flight Declaration credentials getting
        current_app.logging.error('Error in getting Flight Declaration Token')
        current_app.logging.error(e)

    else:    
        my_uploader = flight_declaration_writer.FlightDeclarationsUploader(credentials = fd_credentials)
        my_uploader.upload_to_server(flight_declaration_json=fd)
 


@requires_auth
@requires_scope('blender.write')
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
        flight_declaration_data = req("flight_declaration")

    except KeyError as ke:
        msg = json.dumps({"message":"One parameter are required: observations with a list of observation objects. One or more of these were not found in your JSON request. For sample data see: https://github.com/openskies-sh/airtraffic-data-protocol-development/blob/master/Airtraffic-Data-Protocol.md#sample-traffic-object"})        
        return Response(msg, status=400, mimetype='application/json')

    else:
        task = write_flight_declaration.delay(flight_declaration_data)  # Send a job to the task queuervation)  # Send a job to the task queue

        op = json.dumps ({"message":"OK"})
        return Response(op, status=200, mimetype='application/json')

#### Flight Declaration Module / Endpoint ends

#### Geo Fence Module / Endpoint

@celery.task()
def write_geo_fence(geo_fence): 
    my_credentials = geo_fence_writer.PassportCredentialsGetter()
    credentials = my_credentials.get_cached_credentials()

    my_uploader = geo_fence_writer.GeoFenceUploader(credentials = credentials)
    my_uploader.upload_to_server(gf=geo_fence)


@requires_auth
@requires_scope('blender.write')
@app.route("/submit_geo_fence", methods=['POST'])
def post_geo_fence():   

    try:
        assert request.headers['Content-Type'] == 'application/json'   
    except AssertionError as ae:     
        msg = {"message":"Unsupported Media Type"}
        return Response(json.dumps(msg), status=415, mimetype='application/json')
    else:    
        geo_fence = json.loads(request.data)

    task = write_geo_fence.delay(geo_fence)  # Send a job to the task queue

    op = json.dumps ({"message":"OK"})
    return Response(op, status=200, mimetype='application/json')

#### Geo Fence Module / Endpoint ends

#### DSS RID Module 

@app.route("/")
def home():
    return "Flight Blender"

@requires_auth
@requires_scope('blender.write')
@app.route("/create_dss_subscription", methods=['POST'])
def create_dss_subscription():
    ''' This module takes a lat, lng box from Flight Spotlight and puts in a subscription to the DSS for the ISA '''

    view = request.args.get('view') # view is a bbox list
    
    b = box(view)
    co_ordinates = list(zip(*b.exterior.coords.xy))
    # Convert bounds vertix 
    vertex_list = []
    for cur_co_ordinate in co_ordinates:
        lat_lng = {"lng":0, "lat":0}
        lat_lng["lng"] = cur_co_ordinate[0]
        lat_lng["lat"] = cur_co_ordinate[1]
        vertex_list.append(lat_lng)
    
    vertex_list = []

    # TODO: Make this a asnyc call
    myDSSSubscriber = rid_dss_operations.RemoteIDOperations()
    myDSSSubscriber.create_dss_subscription(vertex_list = vertex_list, view_port = view)
    
    success_msg = json.dumps ({"message":"Subscription Created"})
    return Response(json.dumps(success_msg), status=200, mimetype='application/json')
    

@requires_authority_auth
@requires_scope('dss.write.identification_service_areas')
@app.route("isa_callback/", methods=['POST'])
def dss_isa_callback(id):
    ''' This is the call back end point that other USSes in the DSS network call once a subscription is updated '''
    new_flights_url = request.args.get('flights_url',0)
    try:        
        assert new_flights_url != 0
        redis = redis.Redis(host=app.config['REDIS_HOST'], port =app.config['REDIS_PORT'])   
        # Get the flights URL from the DSS and put it in 
        flights_dict = redis.hgetall("all_uss_flights")        
        all_flights_url = flights_dict['all_flights_url']
        all_flights_url = all_flights_url.append(new_flights_url)
        flights_dict["all_uss_flights"] = all_flights_url
        redis.hmset("all_uss_flights", flights_dict)
        
    except AssertionError as ae:
        return Response("Incorrect data in the POST URL", status=400, mimetype='application/json')
        
    else:
        # All OK return a empty response
        return Response("", status=204, mimetype='application/json')


#### DSS RID Module ends

if __name__ == '__main__':
    app.run(port=8080)