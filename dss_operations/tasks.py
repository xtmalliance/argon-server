from celery.decorators import task
from celery.utils.log import get_task_logger
import logging
from . import dss_rw_helper
from walrus import Database
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())



@task(name='submit_dss_subscription')
def submit_dss_subscription(view , vertex_list):
    myDSSSubscriber = dss_rw_helper.RemoteIDOperations()
    subscription_created = myDSSSubscriber.create_dss_subscription(vertex_list = vertex_list, view_port = view)
    logging.success("Created Subscription %s" % subscription_created.id)


def get_consumer_group(create=False):
    
    db = Database(host=REDIS_HOST, port =REDIS_PORT)   
    stream_keys = ['all_observations']
    
    cg = db.time_series('cg-obs', stream_keys)
    if create:
        for stream in stream_keys:
            db.xadd(stream, {'data': ''})

    if create:
        cg.create()
        cg.set_id('$')

    return cg.all_observations



class AuthorityCredentialsGetter():
    ''' All calls to the DSS require credentials from a authority, usually the CAA since they can provide access to the system '''
    def __init__(self):
        pass
        
    def get_cached_credentials(self, audience):  
        r = redis.Redis()
        
        now = datetime.now()
        cache_key = audience + '_auth_dss_token'
        token_details = r.get(cache_key)
        if token_details:    
            token_details = json.loads(token_details)
            created_at = token_details['created_at']
            set_date = datetime.strptime(created_at,"%Y-%m-%dT%H:%M:%S.%f")
            if now < (set_date - timedelta(minutes=58)):
                credentials = self.get_read_credentials(audience)
                r.set(cache_key, json.dumps({'credentials': credentials, 'created_at':now.isoformat()}))
            else: 
                credentials = token_details['credentials']
        else:               
            credentials = self.get_read_credentials(audience)
            error = credentials.get('error')

            if not error: # there is no error in the token
                    
                r.set(cache_key, json.dumps({'credentials': credentials, 'created_at':now.isoformat()}))            
                r.expire(cache_key, timedelta(minutes=58))
                
        return credentials
            
        
    def get_read_credentials(self, audience):        
        payload = {"grant_type":"client_credentials","client_id": env.get('AUTH_DSS_CLIENT_ID'),"client_secret": env.get('AUTH_DSS_CLIENT_SECRET'),"audience":audience,"scope": 'dss.read_identification_service_areas'}        
        url = env.get('DSS_AUTH_URL') + env.get('DSS_AUTH_TOKEN_URL')        
        token_data = requests.post(url, data = payload)
        t_data = token_data.json()        
        return t_data


@task(name='poll_uss_for_flights')
def poll_uss_for_flights():
    authority_credentials = AuthorityCredentialsGetter()
    flights_dict = redis.hgetall("all_uss_flights")
    all_flights_url = flights_dict['all_flights_url']
    # flights_view = flights_dict['view']
    cg_ops = ConsumerGroupOps()
    cg = cg_ops.get_consumer_group()

    for cur_flight_url in all_flights_url:
        ext = tldextract.extract(cur_flight_url)          
        audience = '.'.join(ext[:3]) # get the subdomain, domain and suffix and create a audience and get credentials
        auth_credentials = authority_credentials.get_cached_credentials(audience)

        headers = {'content-type': 'application/json', 'Authorization': 'Bearer ' + auth_credentials}
    
        flights_response = requests.post(cur_flight_url, headers=headers)
        if flights_response.status_code == 200:
            # https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/uastech/standards/astm_rid_1.0/remoteid/canonical.yaml#tag/p2p_rid/paths/~1v1~1uss~1flights/get
            all_flights = flights_response['flights']
            for flight in all_flights:
                flight_id = flight['id']
                try: 
                    assert flight.get('current_state') is not None
                except AssertionError as ae:
                    current_app.logging.error('There is no current_state provided by SP on the flights url %s' % cur_flight_url)
                    current_app.logging.debug(json.dumps(flight))
                else:
                    position = flight['current_state']['position']
                    now  = datetime.now()
                    time_stamp =  now.replace(tzinfo=timezone.utc).timestamp()
                    
                    if {"lat", "lng", "alt"} <= position.keys():
                        # check if lat / lng / alt existis
                        single_observation = {"icao_address" : flight_id,"traffic_source" :1, "source_type" : 1, "lat_dd" : position['lat'], "lon_dd" : position['lng'], "time_stamp" : time_stamp,"altitude_mm" : position['alt']}
                        # write incoming data directly
                        
                        cg.add(single_observation)    
                    else: 
                        logging.error("Error in received flights data: %{url}s ".format(**flight) ) 
                
        else:
            logging.info(flights_response.status_code) 
