from django.test import TestCase
from django.test import Client

# Create your tests here.
class WeatherMonitoringOperationsTestCase(TestCase):
    def test_get_weather(self):
        c = Client()
        
        response = c.get('/weather_monitoring_ops/weather/')
        
        assert response.status_code == 200
        
        assert response['Content-Type'] == 'application/json'
        
        