<img src="https://i.imgur.com/YIfAsfV.jpg" width="350">

# Flight Blender

Flight Blender is two things:

 - a flight feed aggregator that has different modules that can process and relay data around flights and airspace: geo-fence, flight declarations, air-traffic data
 - an open source Remote ID "display provider" compatible with ASTM Remote ID standard

There are different modules that enable this:

- _Flight Tracking_: It takes in flight tracking feeds from various sources e.g. ADS-B, live telemetry and others and outputs as a single fused JSON feed and submits it to a Display Application e.g. [Flight Spotlight](https://github.com/openskies-sh/flight-spotlight) to be shown in real-time on a display
- _Geofence_: A Geofence can be submitted into Flight Blender and consequently transmitted to Spotlight
- _Flight Declaration_: Future flights up-to 24 hours can be submitted, this __does not__ use the USS <-> USS API but is a standalone component, for supported DSS commands see below
- _DSS Connectivity_: There are modules to connect and read for e.g. Remote ID data from a DSS

## First steps / Get Started

Normally a "Display Provider" is used in conjunction with a "Display Application". In this case Flight Blender output is directed to a Flight Spotlight instance. You can customize a application instance by choosing what kind of modules you want to support, you can pick any or all from the above.

## System Diagram

The diagram below shows how Fight Blender works.

![img](https://i.imgur.com/7Ii62ZD.png)

## Installation

Docker and Docker Compose files are available for this software. You can first clone this repository using `git clone https://www.github.com/openskies-sh/flight-blender.git` and then go to the directory and use `docker-compose up` command.

This will open up port 8080 and you can post air-traffic data to `http://localhost:8080/set_air_traffic` and then start the processing.

## Technical details

- To begin, review the [API Specification](http://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/openskies-sh/flight-blender/master/api/flight-blender-1.0.0-resolved.yaml) to understand the endpoints and the kind of data that you can set in Flight Blender.
- Then take a look at some data formats: [Flight tracking data](https://github.com/openskies-sh/flight-blender/blob/master/importers/air_traffic_samples/micro_flight_data_single.json). This file follows the format as specified in the [Air-traffic data protocol](https://github.com/openskies-sh/airtraffic-data-protocol-development/blob/master/Airtraffic-Data-Protocol.md)

## Submitting AOI, Flight Declarations and Geofence data

Take a look at sample data below to see the kind of data that can be submitted in Flight Blender

- [Area of Interest](https://github.com/openskies-sh/flight-blender/blob/master/importers/aoi_geo_fence_samples/aoi.geojson) as a GeoJSON
- [Geofence](https://github.com/openskies-sh/flight-blender/blob/master/importers/aoi_geo_fence_samples/geo_fence.geojson) as a GeoJSON, we have converters to convert from ED-269
- [Flight Declaration](https://github.com/openskies-sh/flight-blender/blob/master/importers/flight_declarations_samples/flight-1.json). This file follows the format specified in [Flight Declaration Protocol](https://github.com/openskies-sh/flight-declaration-protocol-development)

### Image Credit

<a href="https://www.vecteezy.com/free-vector/blender">Blender Vectors by Vecteezy</a>