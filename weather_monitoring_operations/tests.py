from django.test import TestCase
from django.test import Client
from unittest.mock import patch
from .views import _fetch_weather_data

# Create your tests here.
class WeatherMonitoringOperationsTestCase(TestCase):
    def test_get_weather(self):
        c = Client()
        
        response = c.get('/weather_monitoring_ops/weather/')
        
        print(response.content)
        
        assert response.status_code == 200
        
        assert response['Content-Type'] == 'application/json'

    @patch('requests.get')
    def test_fetch_weather_data(self, mock_get):
        mock_response = {
            'weather': 'sunny',
            'temperature': '70',
            'wind_speed': '10',
            'wind_direction': 'N',
            'precipitation': '0',
            'visibility': '10',
            'cloud_coverage': '0'
        }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response
        
        data = _fetch_weather_data()
        
        assert data == mock_response
        