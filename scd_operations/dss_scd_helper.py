import uuid
import redis, json
import requests
import logging
from dataclasses import asdict
from typing import List
from auth_helper import dss_auth_helper
from .scd_data_definitions import Volume4D, OperationalIntentReference
from os import environ as env
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
 
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

logger = logging.getLogger('django')

class SCDOperations():
    def __init__(self):
        self.dss_base_url = env.get('DSS_BASE_URL')        
        self.r = redis.Redis(host=env.get('REDIS_HOST',"redis"), port =env.get('REDIS_PORT',6379))  
    
    def create_operational_intent_reference(self, state:str, priority:str, volumes:List[Volume4D], off_nominal_volumes:List[Volume4D]):        
        my_authorization_helper = dss_auth_helper.AuthorityCredentialsGetter()
        audience = env.get("DSS_SELF_AUDIENCE", 0)        
        try: 
            assert audience
        except AssertionError as ae:
            logger.error("Error in getting Authority Access Token DSS_SELF_AUDIENCE is not set in the environment")

        try:
            auth_token = my_authorization_helper.get_cached_credentials(audience)
        except Exception as e:
            logger.error("Error in getting Authority Access Token %s " % e)            
        else:
            error = auth_token.get("error")            

        
        # A token from authority was received, we can now submit the operational intent
        new_subscription_id = str(uuid.uuid4())
        dss_subscription_url = self.dss_base_url + 'v1/dss/subscriptions/' + new_subscription_id
        headers = {"Content-Type": "application/json", 'Authorization': 'Bearer ' + auth_token['access_token']}
        management_key = str(uuid.uuid4())
        subscription_id = str(uuid.uuid4())
        blender_base_url = env.get("BLENDER_FQDN", 0)
        payload = {"extents": asdict(volumes[0]), "key":management_key, "priority":priority,"state":state, "uss_base_url":blender_base_url, "subscription_id":subscription_id}
                
        try:
            dss_r = requests.put(dss_subscription_url, json = payload, headers=headers)
        except Exception as re:
            logger.error("Error in putting operational intent in the DSS %s " % re)
            

        try: 
            assert dss_r.status_code == 200            
        except AssertionError as ae:              
            logger.error("Error submitting operational intent to the DSS %s" % dss_r.text)            
        else: 	        
            dss_response = dss_r.json()
            
        