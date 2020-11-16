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
from dss_ops import rid_dss_operations
from stream_helper import ConsumerGroupOps

app = Flask(__name__)
app.config.from_object('config')
app.config["LOG_TYPE"] = os.getenv("LOG_TYPE", "stream")
app.config["LOG_LEVEL"] = os.getenv("LOG_LEVEL", "INFO")

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

# app.celery = celery
import tasks

@app.before_first_request
def initialize_app():
    logs = LogSetup()
    logs.init_app(app)
    # create a consumer group once
    my_cg_ops = ConsumerGroupOps()
    cg = my_cg_ops.get_consumer_group(create=True)


# TODO: Build Flask Blueprints, move the celery calls to their modules. 

#### Airtraffic Endpoint

@requires_auth
@app.route('/set_air_traffic', methods = ['POST'])
def set_air_traffic():
    if requires_scope('blender.write'):
    
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
                task = tasks.write_incoming_data.delay(single_observation)  # Send a job to the task queue

            op = json.dumps ({"message":"OK"})
            return Response(op, status=200, mimetype='application/json')

                    
    raise AuthError({
        "code": "Unauthorized",
        "description": "You don't have access to this resource"
    }, 403)



#### Flight Declaration Module / Endpoint

@requires_auth
@app.route("/submit_flight_declaration", methods=['POST'])
def post_flight_declaration(): 
    if requires_scope('blender.write'):
        try:
            assert request.headers['Content-Type'] == 'application/json'   
        except AssertionError as ae:     
            msg = {"message":"Unsupported Media Type"}
            return Response(json.dumps(msg), status=415, mimetype='application/json')
        else:    
            req = json.loads(request.data)
            
        try:            
            flight_declaration_data = req["flight_declaration"]

        except KeyError as ke:
            msg = json.dumps({"message":"One parameter are required: observations with a list of observation objects. One or more of these were not found in your JSON request. For sample data see: https://github.com/openskies-sh/airtraffic-data-protocol-development/blob/master/Airtraffic-Data-Protocol.md#sample-traffic-object"})        
            return Response(msg, status=400, mimetype='application/json')

        else:
            task = tasks.write_flight_declaration.delay(flight_declaration_data)  # Send a job to the task queuervation)  # Send a job to the task queue
            op = json.dumps ({"message":"Submitted Flight Declaration"})
            return Response(op, status=200, mimetype='application/json')

                    
    raise AuthError({
        "code": "Unauthorized",
        "description": "You don't have access to this resource"
    }, 403)


#### Flight Declaration Module / Endpoint ends

@requires_auth
@app.route("/submit_geo_fence", methods=['POST'])
def post_geo_fence():   

    if requires_scope('blender.write'):
        try:
            assert request.headers['Content-Type'] == 'application/json'   
        except AssertionError as ae:     
            msg = {"message":"Unsupported Media Type"}
            return Response(json.dumps(msg), status=415, mimetype='application/json')
        else:    
            geo_fence = json.loads(request.data)
        
        task = tasks.write_geo_fence.delay(geo_fence)  # Send a job to the task queue

        op = json.dumps ({"message":"Geofence submitted successfully"})
        return Response(op, status=200, mimetype='application/json')
            
    raise AuthError({
        "code": "Unauthorized",
        "description": "You don't have access to this resource"
    }, 403)


#### Geo Fence Module / Endpoint ends

#### DSS RID Module 

@app.route("/")
def home():
    return "Flight Blender"

@requires_auth
@app.route("/create_dss_subscription", methods=['POST'])
def create_dss_subscription():
    ''' This module takes a lat, lng box from Flight Spotlight and puts in a subscription to the DSS for the ISA '''
    if requires_scope('blender.write'):
        try: 
            view = request.args.get('view') # view is a bbox list
            view = [float(i) for i in view.split(",")]
            print(view)
        except Exception as ke:
            incorrect_parameters = {"message":"A view bbox is necessary with four values: minx, miny, maxx and maxy"}
            return Response(json.dumps(incorrect_parameters), status=400, mimetype='application/json')
        else:
            b = box(view[0], view[1], view[2],view[3])
            co_ordinates = list(zip(*b.exterior.coords.xy))
            # Convert bounds vertex list
            vertex_list = []
            for cur_co_ordinate in co_ordinates:
                lat_lng = {"lng":0, "lat":0}
                lat_lng["lng"] = cur_co_ordinate[0]
                lat_lng["lat"] = cur_co_ordinate[1]
                vertex_list.append(lat_lng)
            # remove the final point 
            vertex_list.pop()

            
            # TODO: Make this a asnyc call
            #tasks.submit_dss_subscription(vertex_list = vertex_list, view_port = view)

            myDSSSubscriber = rid_dss_operations.RemoteIDOperations()
            subscription_created = myDSSSubscriber.create_dss_subscription(vertex_list = vertex_list, view_port = view)
            

            success_msg = {"message":"DSS Subscription created"}
            return Response(json.dumps(success_msg), status=200, mimetype='application/json')
            
    raise AuthError({
        "code": "Unauthorized",
        "description": "You don't have access to this resource"
    }, 403)


@requires_authority_auth

@app.route("/isa_callback", methods=['POST'])
def dss_isa_callback(id):
    ''' This is the call back end point that other USSes in the DSS network call once a subscription is updated '''
    if requires_scope('dss.write.identification_service_areas'):
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

    raise AuthError({
        "code": "Unauthorized",
        "description": "You don't have access to this resource"
    }, 403)


#### DSS RID Module ends

if __name__ == '__main__':
    app.run(port=8080)