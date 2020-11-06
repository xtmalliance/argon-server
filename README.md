<img src="https://i.imgur.com/YIfAsfV.jpg" width="350">

# Flight Blender

Flight Blender is a open source Remote ID "display provider" compatible with ASTM standards and a flight feed aggregator. It has different modules that can process and relay data:

- _Flight Tracking_: It takes in flight tracking feeds from various sources e.g. ADS-B, live telemetry and others and outputs as a single fused JSON feed and submits it to a Display Application e.g. [Flight Spotlight](https://github.com/openskies-sh/flight-spotlight) to be shown in real-time on a display
- _Geofence_: A Geofence can be submitted into Flight Blender and consequently transmitted to Spotlight
- _Flight Declaration_: Future flights up-to 24 hours can be submitted, this __does not__ use the USS <-> USS API but is a standalone component, for supported DSS commands see below
- _DSS Connectivity_: There are modules to connect and read for e.g. Remote ID data from a DSS.

## First steps / Get Started

Normally a "Display Provider" is used in conjunction with a "Display Application". In this case Flight Blender output is directed to a Flight Spotlight instance. You can customize a application instance by choosing what kind of modules you want to support, you can pick any from the above.

## System Diagram

The diagram below shows how Fight Blender works. 

![img](https://i.imgur.com/7Ii62ZD.png)

## Installation

Docker and Docker Compose files are available for this software. You can first clone this repository using `git close https://www.github.com/openskies-sh/flight-blender.git` and then go to the directory and use `docker-compose up` command.

This will open up port 8080 and you can post air-traffic data to `http://localhost:8080/set_air_traffic` and then start the processing.

## Technical details

- To begin, review the [API Specification](http://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/openskies-sh/flight-blender/master/api/flight-blender-1.0.0-resolved.yaml) to understand the endpoints and the kind of data that you can set in Flight Blender.
- Then take a look at some data formats: [Flight tracking data](https://github.com/openskies-sh/flight-blender/blob/master/importers/air_traffic_samples/micro_flight_data_single.json). This file follows the format as specified in the [Air-traffic data protocol](https://github.com/openskies-sh/airtraffic-data-protocol-development/blob/master/Airtraffic-Data-Protocol.md)

#### Image Credit

<a href="https://www.vecteezy.com/free-vector/blender">Blender Vectors by Vecteezy</a>
