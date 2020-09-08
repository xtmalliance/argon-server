import time
import requests


def cron_worker():
    print('here')
    print(datetime.now())

def write_incoming_data(observation):            
    msgid = cg.all_observations.add(observation)    
    now = datetime.now()    
        
    try:
        lu = db.get('last-updated')
    except KeyError as e:
        lu = None
    else: 
        lu = datetime.datetime(lu)
    
    if lu is None:
        submit_flights_to_spotlight()
    elif lu > now + timedelta(seconds=5):        
        submit_flights_to_spotlight()
        
    return msgid
