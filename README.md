<img src="https://i.imgur.com/YIfAsfV.jpg" width="350">

# Flight Blender

Flight Blender is a open source "display provider" and a flight feed aggregator. It takes in flight tracking feeds from various sources e.g. ADS-B, DSS and others and outputs as a single fused JSON feed and submits it to a Display Provider e.g. [Flight Spotlight](https://github.com/openskies-sh/flight-spotlight) to be shown in real-time on a display.

## Under the hood

Take a look at the raw files for :

- [Flight tracking data](https://github.com/openskies-sh/flight-blender/blob/master/importers/air_traffic/micro_flight_data_single.json). This file follows the format as specified in the [Airtraffic data protocol](https://github.com/openskies-sh/airtraffic-data-protocol-development/blob/master/Airtraffic-Data-Protocol.md) 
- [Area of Interest](https://github.com/openskies-sh/flight-blender/blob/master/importers/aoi_geo_fence/aoi.geojson) as a GeoJSON
- [Geofence](https://github.com/openskies-sh/flight-blender/blob/master/importers/aoi_geo_fence/geo_fence.geojson) as a GeoJSON, we have converters to convert from ED-269
- [Flight Declaration](https://github.com/openskies-sh/flight-blender/blob/master/importers/flight_declarations/flight-1.json). This file follows the format specified in [Flight Declaration Protocol](https://github.com/openskies-sh/flight-declaration-protocol-development)

#### Image Credit

<a href="https://www.vecteezy.com/free-vector/blender">Blender Vectors by Vecteezy</a>