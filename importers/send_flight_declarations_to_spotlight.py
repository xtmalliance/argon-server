## A file to import flight data into the Secured Flight Spotlight instance. 

import requests 
from dotenv import load_dotenv, find_dotenv
import json
from os import environ as env
from auth_factory import PassportSpotlightCredentialsGetter, NoAuthCredentialsGetter

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

class FlightSpotlightUploader():
    
    def __init__(self, credentials):
    
        self.credentials = credentials
    
    def upload_to_server(self, filename):
        with open(filename, "r") as flight_declaration_file:
            flight_declaration_json = flight_declaration_file.read()
            
        flight_declaration_data = json.loads(flight_declaration_json)
        # print (flight_declaration_data['flight_declaration']['parts'])

        headers = {"Authorization": "Bearer "+ self.credentials['access_token']}
        
        payload = {"flight_declaration" : json.dumps(flight_declaration_data)}                

        securl = env.get('FLIGHT_SPOTLIGHT_URL') + '/set_flight_declaration'
        try:
            response = requests.post(securl, data= payload, headers=headers)
            print(response.content)                
        except Exception as e:
            print(e)
        else:
            print("Uploaded Flight Declarations")                    

if __name__ == '__main__':
    # my_credentials = PassportSpotlightCredentialsGetter()
    my_credentials = NoAuthCredentialsGetter()
    credentials = my_credentials.get_cached_credentials(audience='testflight.flightspotlight.com', scopes=['spotlight.write'])
        
    my_uploader = FlightSpotlightUploader(credentials = credentials)
    my_uploader.upload_to_server(filename='flight_declarations_samples/flight-1.json')