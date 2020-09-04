import time
import requests
from walrus import Database

    
db = Database()   

stream_keys = ['observations']
for stream in stream_keys:
    db.xadd(stream, {'data': ''})
 
cg = db.time_series('obs', stream_keys)
cg.create()  # Create the consumer group.
cg.set_id('$')


def submit_flights_to_spotlight():
    status = 1

    all_messages = cg.observations.read(block=2000, last_id='$')

    for message in all_messages:
        headers = {}
        payload = message
        # payload = {"icao_address" : icao_address,"traffic_source" :traffic_source, "source_type" : source_type, "lat_dd" : lat_dd, "lon_dd" : lon_dd, "time_stamp" : time_stamp,"altitude_mm" : altitude_mm}
        securl = 'http://localhost:5000/set_air_traffic'
        response = requests.post(securl, data= payload, headers=headers)
        

    for msg_id, _, _, _ in cg.observations.pending():
        cg.observations.ack(msg_id)
    
    cg.set_id(id='$')
    

    return status

def write_incoming_data(observation):        
    msgid = cg.observations.add(observation)
    return msgid


