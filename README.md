<img src="https://i.imgur.com/YIfAsfV.jpg" width="350">

# Flight Blender

Flight Blender is a open source "display provider" and a flight feed aggregator. It has different modules that can relay data in to a display such as [Flight Spotlight](https://github.com/openskies-sh/flight-spotlight). Some modules: 
- _Flight Tracking_: It takes in flight tracking feeds from various sources e.g. ADS-B, DSS and others and outputs as a single fused JSON feed and submits it to a Display Provider e.g. [Flight Spotlight](https://github.com/openskies-sh/flight-spotlight) to be shown in real-time on a display.
- _Geofence_: A Geofence can be submitted into Flight Blender and consequently transmitted to Spotlight
- _Flight Declaration_: Future flights up-to 24 hours can be submitted
- _DSS Connectivity_: There are modules to connect and read for e.g. Remote ID data from a DSS.

## First steps / Get Started

Review the [API Specification](http://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/openskies-sh/flight-blender/master/api/flight-blender-1.0.0-resolved.yaml) to understand the endpoints and the kind of data that you can set in Flight Blender


## Installation

Docker and Docker Compose files are available for this software. You can first clone this repository using `git close https://www.github.com/openskies-sh/flight-blender.git` and then go to the directory and use `docker-compose up` command.

This will open up port 8080 and you can post air-traffic data to `http://localhost:8080/set_air_traffic` and then start the processing.

## Under the hood

Take a look at the raw files for :

- [Flight tracking data](https://github.com/openskies-sh/flight-blender/blob/master/importers/air_traffic_samples/micro_flight_data_single.json). This file follows the format as specified in the [Air-traffic data protocol](https://github.com/openskies-sh/airtraffic-data-protocol-development/blob/master/Airtraffic-Data-Protocol.md)

#### Image Credit

<a href="https://www.vecteezy.com/free-vector/blender">Blender Vectors by Vecteezy</a>