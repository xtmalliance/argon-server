## A module to read data from a DSS, this specifically implements the Remote ID standard as released on Oct-2020
## For more information review: https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/uastech/standards/astm_rid_1.0/remoteid/canonical.yaml 
## and this diagram https://github.com/interuss/dss/blob/master/assets/generated/rid_display.png

from functools import wraps
import json
import redis
import hashlib
import logging
from datetime import datetime, timedelta
import uuid, os
import requests
from os import environ as env

class AuthorityCredentialsGetter():
    ''' All calls to the DSS require credentials from a authority, usually the CAA since they can provide access to the system '''
    def __init__(self):
        pass
        
    def get_cached_credentials(self, audience):  
        r = redis.Redis(host=env.get('REDIS_HOST',"redis"), port =env.get('REDIS_PORT',6379))   
        
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
        
        self.redis = redis.Redis(host=env.get('REDIS_HOST',"redis"), port =env.get('REDIS_PORT',6379))  

    def create_dss_subscription(self, vertex_list, view, request_uuid):
        ''' This method PUTS /dss/subscriptions ''' 
        
        subscription_response = {"created": 0, "subscription_id": 0, "notification_index": 0}
            
        my_authorization_helper = AuthorityCredentialsGetter()
        audience = env.get("DSS_SELF_AUDIENCE", 0)
        error = None

        try: 
            assert audience
        except AssertionError as ae:
            logging.error("Error in getting Authority Access Token DSS_SELF_AUDIENCE is not set in the environment")
            return subscription_response

        try:
            auth_token = my_authorization_helper.get_cached_credentials(audience)
        except Exception as e:

            logging.error("Error in getting Authority Access Token %s " % e)
            return subscription_response        
        else:
            error = auth_token.get("error")            
        
        try: 
            assert error is None
        except AssertionError as ae:             
            return subscription_response
        else: 
            
            logging.info("Successfully received Token")
            # A token from authority was received, 
            new_subscription_id = str(uuid.uuid4())
            dss_subscription_url = self.dss_base_url + '/dss/subscriptions/' + new_subscription_id
            
            # check if a subscription already exists for this view_port


            callback_url = env.get("SUBSCRIPTION_CALLBACK_URL","/uss/identification_service_areas") 
            now = datetime.now()

            callback_url += '/'+ new_subscription_id
            
            current_time = now.isoformat()
            three_mins_from_now = (now + timedelta(minutes=3)).isoformat()

            headers = {'content-type': 'application/json', 'Authorization': 'Bearer ' + auth_token}

            volume_object = {"spatial_volume":{"footprint":{"vertices":vertex_list},"altitude_lo":0.5,"altitude_hi":400},"time_start":current_time,"time_end":three_mins_from_now }
            
            payload = {"extents": volume_object, "callbacks":{"identification_service_area_url":callback_url}}

            try:
                dss_r = requests.put(dss_subscription_url, data= json.dumps(payload), headers=headers)  
            except Exception as re: 
                logging.error("Error in posting to subscription URL %s " % re)
                return subscription_response

            else: 
                try: 
                    assert dss_r.status_code == 200
                    subscription_response["created"] = 1
                except AssertionError as ae:              
                    logging.error("Error in creating subscription in the DSS %s" % dss_r.text)
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

                    flights_dict = {'request_id':request_uuid, 'subscription_id': subscription_id,'all_flights_url':flights_url_list, 'notification_index': notification_index, 'view':view, 'expire_at': three_mins_from_now}
 
                    hash_name = "all_uss_flights-" + new_subscription_id
                    self.redis.hmset(hash_name, flights_dict)
                    # expire keys in three minutes 
                    self.redis.expire(name=hash_name, time=timedelta(minutes=3))
                    return subscription_response


    def delete_dss_subscription(self,subscription_id):
        ''' This module calls the DSS to delete a subscription''' 

        # TODO: Subscriptions expire after a hour but we may need to delete one 
        

