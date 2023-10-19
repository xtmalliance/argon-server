from django.http import JsonResponse
import json
import requests

def get_weather_data(request):
    
    data = {
        "weather": "sunny",
        "temperature": "70",
        "wind_speed": "10",
        "wind_direction": "N",
        "precipitation": "0",
        "visibility": "10",
        "cloud_coverage": "0"
    }
    
    json_data = json.dumps(data)
    
    return JsonResponse(json_data, safe=False)

def _fetch_weather_data():
    weather_data_response = requests.get('https://api.open-meteo.com/v1/forecast?latitude=24.4512&longitude=54.397&hourly=temperature_2m&forecast_days=1')
    
    if weather_data_response.status_code == 200:
        return weather_data_response.json()
    else:
        
        raise Exception("Error fetching weather data")