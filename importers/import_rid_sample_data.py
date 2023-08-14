import os
import json
from os.path import dirname, abspath
import  time
import requests
from dataclasses import dataclass, asdict
from typing import Optional
from auth_factory import PassportCredentialsGetter, NoAuthCredentialsGetter
from dacite import from_dict
from rid_definitions import LatLngPoint, RIDOperatorDetails, UASID, OperatorLocation, UAClassificationEU

class BlenderUploader():
    
    def __init__(self, credentials):        
    
        self.credentials = credentials
    
    def upload_to_server(self, filename):
        with open(filename, "r") as rid_json_file:
            rid_json = rid_json_file.read()
            
        rid_json = json.loads(rid_json)
        
        states = rid_json['current_states']
        rid_operator_details  = rid_json['flight_details']
        
        uas_id = UASID(registration_id = 'CHE-5bisi9bpsiesw',  serial_number='d29dbf50-f411-4488-a6f1-cf2ae4d4237a',utm_id= '07a06bba-5092-48e4-8253-7a523f885bfe')
        # eu_classification =from_dict(data_class= UAClassificationEU, data= rid_operator_details['rid_details']['eu_classification'])      
        eu_classification = UAClassificationEU()
        operator_location = OperatorLocation(position = LatLngPoint(lat = 46.97615311620088,lng = 7.476099729537965))
        rid_operator_details = RIDOperatorDetails(
            id= "382b3308-fa11-4629-a966-84bb96d3b4db",
            uas_id = uas_id,
            operation_description="Medicine Delivery",
            operator_id='CHE-076dh0dq',
            eu_classification = eu_classification,            
            operator_location=  operator_location
        )
        for state in states: 
            headers = {"Content-Type":'application/json',"Authorization": "Bearer "+ self.credentials['access_token']}            
            # payload = {"observations":[{"icao_address" : icao_address,"traffic_source" :traffic_source, "source_type" : source_type, "lat_dd" : lat_dd, "lon_dd" : lon_dd, "time_stamp" : time_stamp,"altitude_mm" : altitude_mm, 'metadata':metadata}]}            

            payload = {"observations":[{"current_states":[state], "flight_details": {"rid_details" :asdict(rid_operator_details), "aircraft_type": "Helicopter","operator_name": "Thomas-Roberts" }}]}            
            securl = 'http://localhost:8000/flight_stream/set_telemetry' # set this to self (Post the json to itself)
            try:
                response = requests.put(securl, json = payload, headers = headers)
                
            except Exception as e:                
                print(e)
            else:
                if response.status_code == 201:
                    print("Sleeping 3 seconds..")
                    time.sleep(3)
                else: 
                    print(response.json())


if __name__ == '__main__':
    

    # my_credentials = PassportCredentialsGetter()
    my_credentials = NoAuthCredentialsGetter()    
    credentials = my_credentials.get_cached_credentials(audience='testflight.flightblender.com', scopes=['blender.write'])
    parent_dir = dirname(abspath(__file__))  #<-- absolute dir the raw input file  is in
    
    rel_path = "rid_samples/flight_1_rid_aircraft_state.json"
    abs_file_path = os.path.join(parent_dir, rel_path)
    my_uploader = BlenderUploader(credentials=credentials)
    my_uploader.upload_to_server(filename=abs_file_path)