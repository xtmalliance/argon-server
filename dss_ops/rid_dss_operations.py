## A module to read data from a DSS, this specifically implements the Remote ID standard as released on Oct-2020
## For more information review: https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/uastech/standards/astm_rid_1.0/remoteid/canonical.yaml 
## and this diagram https://github.com/interuss/dss/blob/master/assets/generated/rid_display.png

from functools import wraps
import json
from flask_uuid import FlaskUUID
from six.moves.urllib.request import urlopen

import redis
from datetime import datetime, timedelta
import uuid, os
import requests
from flask import request
from Flask import current_app
from os import environ as env
# from flask import Blueprint
# dss_rid_blueprint = Blueprint('rid_dss_operations_bp', __name__)

REDIS_HOST = os.getenv('REDIS_HOST',"redis")
REDIS_PORT = 6379

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
            access_token = credentials.get('access_token')
            if access_token: # there is no error in the token
                r.set(cache_key, json.dumps({'credentials': credentials, 'created_at':now.isoformat()}))            
                r.expire(cache_key, timedelta(minutes=58))
                
        return credentials
            
        
    def get_read_credentials(self, audience):        
        payload = {"grant_type":"client_credentials","client_id": env.get('AUTH_DSS_CLIENT_ID'),"client_secret": env.get('AUTH_DSS_CLIENT_SECRET'),"audience":audience,"scope": 'dss.read_identification_service_areas'}        
        url = env.get('DSS_AUTH_URL') + env.get('DSS_AUTH_TOKEN_ENDPOINT')        
        token_data = requests.post(url, data = payload)
        t_data = token_data.json()        
        return t_data

class RemoteIDOperations():

    def __init__(self):
        self.dss_base_url = env.get('DSS_BASE_URL')

    def create_dss_subscription(self, vertex_list, view_port):
        ''' This method PUTS /dss/subscriptions ''' 
        
        subscription_response = {"created": 0, "subscription_id": 0, "notification_index": 0}
            
        my_authorization_helper = AuthorityCredentialsGetter()
        audience = env.get("SELF_DSS_AUDIENCE", 0)
        if audience == 0:
            current_app.logging.error("Error in getting Authority Access Token SELF_DSS_AUDIENCE is not set in the environment")
        else:
            auth_token = my_authorization_helper.get_cached_credentials(audience)
            error = auth_token.get("error")
            
        try: 
            assert error is None
        except AssertionError as ae: 
            current_app.logger.error("Error in getting Authority Access Token %s": % auth_token)
            return subscription_response
        else: 
            current_app.logger.info("Successfully received Token")
            # A token from authority was received, 
            new_subscription_id = str(uuid.uuid4())
            dss_subscription_url = self.dss_base_url + '/dss/subscriptions/' + new_subscription_id

            callback_url = env.get("SUBSCRIPTION_CALLBACK_URL","/isa_callback") 
            now = datetime.now()
            
            current_time = now.isoformat()
            one_hour_from_now = (now + timedelta(hours=1)).isoformat()

            headers = {'content-type': 'application/json', 'Authorization': 'Bearer ' + auth_token}

            volume_object = {"spatial_volume":{"footprint":{"vertices":vertex_list},"altitude_lo":0.5,"altitude_hi":400},"time_start":current_time,"time_end":one_hour_from_now }
            
            payload = {"extents": volume_object, "callbacks":{"identification_service_area_url":callback_url}}

            dss_r = requests.post(dss_subscription_url, data= json.dumps(payload), headers=headers)   
            
            try: 
                assert dss_r.status_code == 200
                subscription_response["created"] = 1
            except AssertionError as ae: 
                current_app.logger.error("Error in creating subscription in the DSS %s" % r.text)
                return subscription_response
            else: 	
                dss_response = dss_r.json()
                service_areas = dss_response['service_areas']
                subscription = dss_response['subscription']
                subscription_id = subscription['id']
                notification_index = subscription['notification_index']
                subscription_response['notification_index'] = notification_index
                subscription_response['subscription_id'] = subscription_id
                # iterate over the service areas to get flights URL to poll 
                
                flights_url_list = []
                for service_area in service_areas: 
                    flights_url = service_area['flights_url']
                    flights_url_list.append(flights_url)

                flights_dict= {'subscription_id': subscription_id,'all_flights_url':flights_url_list, 'notification_index': notification_index, 'view':view_port, 'expire_at':one_hour_from_now}

                redis = redis.Redis()
                hash_name = "all_uss_flights"
                redis.hmset(hash_name, flights_dict)
                # expire keys in one hour
                redis.expire(name=hash_name, time=timedelta(minutes=60))
                return subscription_response


    def delete_dss_subscription(self,subscription_id):
        ''' This module calls the DSS to delete a subscription''' 

        # TODO: Subscriptions expire after a hour but we may need to delete one 
        pass
