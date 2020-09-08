import celery

@celery.task()
def print_hello():
    logger = print_hello.get_logger()
    logger.info("Hello")
    
@celery.task()
def submit_flights_to_spotlight():
    status = 1
    # get existing consumer group
    
    
    messages = cg.all_observations.read()
    pending_messages = []
    for message in messages: 
        pending_messages.append({'timestamp': message.timestamp,'seq': message.sequence, 'data':message.data, 'address':message.data['icao_address']})
    
    # sort by date
    pending_messages.sort(key=lambda item:item['timestamp'], reverse=True)

    # Keep only the latest message
    distinct_messages = {i['address']:i for i in reversed(pending_messages)}.values()

    for message in distinct_messages:
        # headers = {}
        # payload = message
        # print(message)
        payload = {"icao_address" : message['icao_address'],"traffic_source" :message['traffic_source'], "source_type" : message['source_type'], "lat_dd" : message['lat_dd'], "lon_dd" : message['lon_dd'], "time_stamp" : message['time_stamp'],"altitude_mm" : message['altitude_mm']}
        print(payload)
        # securl = 'http://localhost:5000/set_air_traffic'
        # response = requests.post(securl, data= payload, headers=headers)


    return status

