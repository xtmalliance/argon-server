from flask import Flask, url_for
from flask import render_template
from functools import wraps
from flask import request, Response
import requests, json
import logging
import redis
from rq import Queue
from rq_scheduler import Scheduler
import time
from utils import submit_flights_to_spotlight, write_incoming_data
from worker import conn
from walrus import Database
app = Flask(__name__)

q = Queue(connection=conn)
scheduler = Scheduler(queue=q)

@app.route("/initialize", methods = ['POST'])
def initialize():            
    stream_keys = ['observations']
    db = Database()    
    cg = db.consumer_group('cg-observations', stream_keys)
    cg.create()  # Create the consumer group.
    cg.set_id('$')


@app.route("/blend", methods = ['POST'])
def blend():    
    cron_string = '*/5 * * * *' # 5 seconds

    scheduler.cron(
        cron_string,                # A cron string (e.g. "0 0 * * 0")
        func=submit_flights_to_spotlight,                  # Function to be queued
        repeat=None,                  # Repeat this number of times (None means repeat forever)
        queue_name=q,      # In which queue the job should be put in
    )

    msg = {"status":"OK"}
    return Response(msg, status=200, mimetype='application/json')


@app.route("/stop_blend", methods = ['POST'])
def stop_blend():
    list_of_job_instances = scheduler.get_jobs()
    for job in list_of_job_instances:
        scheduler.cancel(job)

    msg = {"status":"OK"}
    return Response(msg, status=200, mimetype='application/json')


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
            task = q.enqueue(write_incoming_data, single_observation)  # Send a job to the task queue

            jobs = q.jobs  # Get a list of jobs in the queue

            q_len = len(q)  # Get the queue length

            message = f"Task queued at {task.enqueued_at.strftime('%a, %d %b %Y %H:%M:%S')}. {q_len} jobs queued"


    op = json.dumps ({"message":"OK" , "status":message})
    return Response(op, status=200, mimetype='application/json')

if __name__ == '__main__':
    app.run()