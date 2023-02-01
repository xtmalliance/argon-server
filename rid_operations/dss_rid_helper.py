## A module to read data from a DSS, this specifically implements the Remote ID standard as released on Oct-2020
## For more information review: https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/uastech/standards/astm_rid_1.0/remoteid/canonical.yaml 
## and this diagram https://github.com/interuss/dss/blob/master/assets/generated/rid_display.png

from rid_operations.rid_utils import SubscriptionResponse
import logging
from datetime import datetime, timedelta
import uuid
from auth_helper import dss_auth_helper
import json
from auth_helper.common import get_redis
import requests
import hashlib
import tldextract
from os import environ as env
from dotenv import load_dotenv, find_dotenv
from dataclasses import asdict
from datetime import timedelta
from .rid_utils import SubscriberToNotify, SubscriptionState, Volume4D, ISACreationRequest, ISACreationResponse, IdentificationServiceArea
from typing import List
logger = logging.getLogger('django')
load_dotenv(find_dotenv())
 
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

class RemoteIDOperations():

    def __init__(self):
        self.dss_base_url = env.get('DSS_BASE_URL', 0)
        self.r = get_redis()


    def create_dss_isa(self, flight_extents:Volume4D,flights_url :str , expiration_time_seconds: int = 30) -> ISACreationResponse:
        ''' This method PUTS /dss/subscriptions ''' 
        
        # subscription_response = {"created": 0, "subscription_id": 0, "notification_index": 0}
        isa_creation_response = ISACreationResponse(created=0,service_area= None, subscribers=[])
        new_isa_id = str(uuid.uuid4())
        
        my_authorization_helper = dss_auth_helper.AuthorityCredentialsGetter()
        audience = env.get("DSS_SELF_AUDIENCE", 0)        
        error = None

        try: 
            assert audience
        except AssertionError as ae:
            logger.error("Error in getting Authority Access Token DSS_SELF_AUDIENCE is not set in the environment")
            return isa_creation_response

        try:
            auth_token = my_authorization_helper.get_cached_credentials(audience = audience, token_type='rid')
        except Exception as e:
            logger.error("Error in getting Authority Access Token %s " % e)
            return isa_creation_response        
        else:
            error = auth_token.get("error")            
        
        try: 
            assert error is None
        except AssertionError as ae:             
            return isa_creation_response
        else:                        
            # A token from authority was received, 
            
            dss_isa_create_url = self.dss_base_url + 'v1/dss/identification_service_areas/' + new_isa_id
            
            # check if a subscription already exists for this view_port           
            
            headers = {'content-type': 'application/json', 'Authorization': 'Bearer ' + auth_token['access_token']}
            p = ISACreationRequest(extents= flight_extents, flights_url= flights_url)
            p_dict = asdict(p)
            try:
                dss_r = requests.put(dss_isa_create_url, json= json.loads(json.dumps(p_dict)), headers=headers)
            except Exception as re:
                logger.error("Error in posting to subscription URL %s " % re)
                return isa_creation_response

            try: 
                assert dss_r.status_code == 200
                isa_creation_response.created = 1
            except AssertionError as ae:              
                logger.error("Error in creating ISA in the DSS %s" % dss_r.text)
                return isa_creation_response
            else: 	        
                dss_response = dss_r.json()
                dss_response_service_area = dss_response['service_area']
                service_area = IdentificationServiceArea(flights_url= dss_response_service_area['flights_url'], owner=dss_response_service_area['owner'], time_start=dss_response_service_area['time_start'], time_end=dss_response_service_area['time_end'], version= dss_response_service_area['version'], id = dss_response_service_area['id'])
                
                # TODO : Notify subscribers 
                dss_response_subscribers = dss_response['subscribers']

                dss_r_subs:List[SubscriberToNotify] = []
                for subscriber in dss_response_subscribers:
                    subs = subscriber['subscriptions']
                    all_s = []
                    for sub in subs: 
                        s = SubscriptionState(subscription_id=sub['subscription_id'],notification_index=sub['notification_index'])
                        all_s.append(s)

                    subscriber_to_notify = SubscriberToNotify(url = subscriber['url'],subscriptions=all_s)
                    dss_r_subs.append(subscriber_to_notify)

                for subscriber in dss_r_subs:                    
                    url = '{}/{}'.format(subscriber.url, new_isa_id)
               
                    try:
                        ext = tldextract.extract(subscriber.url)  
                    except Exception as e: 
                        uss_audience = 'localhost'
                    else:
                        if ext.domain in ['localhost', 'internal']:# for host.docker.internal type calls
                            uss_audience = 'localhost'
                        else:
                            uss_audience = '.'.join(ext[:3]) # get the subdomain, domain and suffix and create a audience and get credentials
                    
                    uss_auth_token = self.get_auth_token(audience = uss_audience)          
                    
                    # Notify subscribers
                    payload = {
                            'service_area': service_area,
                            'subscriptions': subscriber.subscriptions,
                            'extents': json.loads(json.dumps(asdict(flight_extents)))
                    }
                        
                    auth_credentials = my_authorization_helper.get_cached_credentials(audience = uss_audience, token_type='rid')            
                    headers = {'content-type': 'application/json', 'Authorization': 'Bearer ' + auth_credentials['access_token']}                        
                    try: 
                        notification_request = requests.post(url, headers=headers, json =json.loads(json.dumps(payload)))                            
                    except Exception as re:
                        logger.error("Error in sending subscriber notification to %s :  %s " % (url, re))
                    
                    
                    


                logger.info("Succesfully created a DSS ISA %s" % new_isa_id)
                # iterate over the service areas to get flights URL to poll       
                isa_key = 'isa-' + service_area.id                
                isa_seconds_timedelta = timedelta(seconds=expiration_time_seconds)
                self.r.set(isa_key, 1)
                self.r.expire(name = isa_key, time = isa_seconds_timedelta)
                isa_creation_response.created =1 
                isa_creation_response.service_area = service_area
                isa_creation_response.subscribers = dss_r_subs


                return asdict(isa_creation_response)

    def create_dss_subscription(self, vertex_list:list, view:str, request_uuid, subscription_time_delta: int=30):
        ''' This method PUTS /dss/subscriptions ''' 
        
        # subscription_response = {"created": 0, "subscription_id": 0, "notification_index": 0}
        subscription_response = SubscriptionResponse(created=0,dss_subscription_id = None, notification_index=0)
         
        my_authorization_helper = dss_auth_helper.AuthorityCredentialsGetter()
        audience = env.get("DSS_SELF_AUDIENCE", 0)        
        error = None

        try: 
            assert audience
        except AssertionError as ae:
            logger.error("Error in getting Authority Access Token DSS_SELF_AUDIENCE is not set in the environment")
            return subscription_response

        try:
            auth_token = my_authorization_helper.get_cached_credentials(audience = audience, token_type='rid')
        except Exception as e:
            logger.error("Error in getting Authority Access Token %s " % e)
            return subscription_response        
        else:
            error = auth_token.get("error")            
        
        try: 
            assert error is None
        except AssertionError as ae:             
            return subscription_response
        else:                        
            # A token from authority was received, 
            new_subscription_id = str(uuid.uuid4())
            dss_subscription_url = self.dss_base_url + 'v1/dss/subscriptions/' + new_subscription_id
            
            # check if a subscription already exists for this view_port
            
            callback_url = env.get("BLENDER_FQDN","https://www.flightblender.com") + "/dss/identification_service_areas" 
            now = datetime.now()

            callback_url += '/'+ new_subscription_id
            subscription_seconds_timedelta = timedelta(seconds=subscription_time_delta)
            current_time = now.isoformat() + 'Z'
            fifteen_seconds_from_now = now + subscription_seconds_timedelta
            fifteen_seconds_from_now_isoformat = fifteen_seconds_from_now.isoformat() +'Z'
            headers = {'content-type': 'application/json', 'Authorization': 'Bearer ' + auth_token['access_token']}
            volume_object = {"spatial_volume":{"footprint":{"vertices":vertex_list},"altitude_lo":0.5,"altitude_hi":800},"time_start":current_time,"time_end":fifteen_seconds_from_now_isoformat }
            
            payload = {"extents": volume_object, "callbacks":{"identification_service_area_url":callback_url}}

            try:
                dss_r = requests.put(dss_subscription_url, json= payload, headers=headers)
            except Exception as re:
                logger.error("Error in posting to subscription URL %s " % re)
                return subscription_response

            try: 
                assert dss_r.status_code == 200
                subscription_response.created = 1
            except AssertionError as ae:              
                logger.error("Error in creating subscription in the DSS %s" % dss_r.text)
                return subscription_response
            else: 	        
                dss_response = dss_r.json()
                
                service_areas = dss_response['service_areas']
                dss_subscription_details = dss_response['subscription']
                subscription_id = dss_subscription_details['id']
                notification_index = dss_subscription_details['notification_index']
                new_subscription_version = dss_subscription_details['version']
                subscription_response.notification_index = notification_index
                subscription_response.dss_subscription_id = subscription_id        
                # logger.info("Succesfully created a DSS subscription ID %s" % subscription_id)
                # iterate over the service areas to get flights URL to poll 
                flights_url_list = ''
                
                for service_area in service_areas: 
                    flights_url = service_area['flights_url']
                    flights_url_list += flights_url +'?view='+ view + ' '

                flights_dict = {'request_id': request_uuid, 'subscription_id': subscription_id,'all_flights_url': flights_url_list, 'notification_index': notification_index, 'view': view, 'expire_at': fifteen_seconds_from_now_isoformat, 'version': new_subscription_version}

                subscription_id_flights = "all_uss_flights:" + new_subscription_id 
                
                self.r.hmset(subscription_id_flights, flights_dict)
                # expire keys in fifteen seconds                                 
                self.r.expire(name = subscription_id_flights,  time = subscription_seconds_timedelta)  
                
                sub_id = 'sub-' + request_uuid

                self.r.set(sub_id, view)
                self.r.expire(name = sub_id, time = subscription_seconds_timedelta)

                view_hash = int(hashlib.sha256(view.encode('utf-8')).hexdigest(), 16) % 10**8            
                view_sub = 'view_sub-' + str(view_hash)                
                self.r.set(view_sub, 1)
                self.r.expire(name = view_sub, time =subscription_seconds_timedelta)

                return subscription_response

    def delete_dss_subscription(self,subscription_id):
        ''' This module calls the DSS to delete a subscription''' 

        pass

    def query_uss_for_rid(self, flights_dict, all_observations, subscription_id:str):
        
        authority_credentials = dss_auth_helper.AuthorityCredentialsGetter()        
        all_flights_urls_string = flights_dict['all_flights_url']        
        logging.debug("Flight url list : %s" % all_flights_urls_string)
        all_flights_url = all_flights_urls_string.split()        
        for cur_flight_url in all_flights_url:
            try:
                ext = tldextract.extract(cur_flight_url)  
            except Exception as e: 
                audience == 'localhost'
            else:
                if ext.domain in ['localhost', 'internal']:# for allowing host.docker.internal setup as well
                    audience = 'localhost'
                else:
                    audience = '.'.join(ext[:3]) # get the subdomain, domain and suffix and create a audience and get credentials
            
            auth_credentials = authority_credentials.get_cached_credentials(audience = audience, token_type='rid')            
            headers = {'content-type': 'application/json', 'Authorization': 'Bearer ' + auth_credentials['access_token']}                        
            flights_request = requests.get(cur_flight_url, headers=headers)
            
            if flights_request.status_code == 200:
                # https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/uastech/standards/astm_rid_1.0/remoteid/canonical.yaml#tag/p2p_rid/paths/~1v1~1uss~1flights/get
                flights_response = flights_request.json()                
                all_flights = flights_response['flights']
                for flight in all_flights:
                    flight_id = flight['id']                    
                    try: 
                        assert flight.get('current_state') is not None
                    except AssertionError as ae:
                        logger.error('There is no current_state provided by SP on the flights url %s' % cur_flight_url)
                        logger.debug(json.dumps(flight))
                    else:
                        flight_current_state = flight['current_state']
                        position = flight_current_state['position']       
                        
                        recent_positions = flight['recent_positions'] if 'recent_positions' in flight.keys() else []                                       
                        
                        flight_metadata = {'id':flight_id,"simulated": flight["simulated"],"aircraft_type":flight["aircraft_type"],'subscription_id':subscription_id, "current_state":flight_current_state,"recent_positions":recent_positions }
                        # logger.info("Writing flight remote-id data..")
                        if {"lat", "lng", "alt"} <= position.keys():
                            # check if lat / lng / alt existis
                            single_observation = {"icao_address" : flight_id,"traffic_source" :1, "source_type" : 1, "lat_dd" : position['lat'], "lon_dd" : position['lng'], "altitude_mm" : position['alt'],'metadata':json.dumps(flight_metadata)}
                            # write incoming data directly
                            all_observations.add(single_observation)                               
                            all_observations.trim(1000)                             
                        else: 
                            logger.error("Error in received flights data: %{url}s ".format(**flight)) 
                    
            else:
                logs_dict = {'url':cur_flight_url, 'status_code':flights_request.status_code}
                logger.info("Received a non 200 error from {url} : {status_code} ".format(**logs_dict))
                logger.info("Detailed Response %s" % flights_request.text) 
                

