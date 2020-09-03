import time
import requests
from walrus import Database

db = Database()
stream = db.Stream('observation') 

def submit_flights_to_spotlight():
    status = 1


    return status

def write_incoming_data(observation):    
    
    msgid = stream.add(observation)

    return msgid


