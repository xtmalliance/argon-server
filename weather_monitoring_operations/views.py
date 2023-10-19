from django.http import HttpResponse

def get_weather_data(request):
    return HttpResponse('Hello, world. You\'re at the weather_monitoring_operations index.')