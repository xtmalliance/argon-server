from django.http import JsonResponse
import json 

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