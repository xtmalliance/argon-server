## A file to import flight data into the Tile 38 instance. 
import os
import json, time, requests
from os.path import dirname, abspath
class BlenderUploader():
    
    def __init__(self):        
        
        self.timestamps = [1590000000000,1590000005000,1590000010000,1590000015000,1590000020000]    
    
    def upload_to_server(self, filename):
        with open(filename, "r") as traffic_json_file:
            traffic_json = traffic_json_file.read()
            
        traffic_json = json.loads(traffic_json)
        
       
        for timestamp in self.timestamps: 
            
            current_timestamp_readings =  [x for x in traffic_json if x['timestamp'] == timestamp]
            
            for current_reading in current_timestamp_readings:
                icao_address = current_reading['icao_address']
                traffic_source = current_reading["traffic_source"]
                source_type = current_reading["source_type"]
                lat_dd = current_reading['lat_dd']
                lon_dd = current_reading['lon_dd']
                time_stamp = current_reading['timestamp']
                altitude_mm = current_reading['altitude_mm']
                # print(timestamp)
                headers = {"Content-Type":'application/json'}
                payload = {"observations":[{"icao_address" : icao_address,"traffic_source" :traffic_source, "source_type" : source_type, "lat_dd" : lat_dd, "lon_dd" : lon_dd, "time_stamp" : time_stamp,"altitude_mm" : altitude_mm}]}
                
                securl = 'http://localhost:8080/set_air_traffic' # set this to self (Post the json to itself)
                try:
                    response = requests.post(securl, data= json.dumps(payload), headers= headers)
                    print(response.content)                
                except Exception as e:
                    print(e)
                else:
                    print("Sleeping 25 seconds..")
                    time.sleep(25)


if __name__ == '__main__':
    
    parent_dir = dirname(abspath(__file__) #<-- absolute dir the raw input file  is in
    rel_path = "air_traffic_samples/micro_flight_data_single.json"
    abs_file_path = os.path.join(parent_dir, rel_path)
    my_uploader = BlenderUploader()
    my_uploader.upload_to_server(filename=abs_file_path)