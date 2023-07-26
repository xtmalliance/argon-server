<img src="images/blender-logo.jpg" width="350">

# Flight Blender

Flight Blender is a backend / data-processing engine that to stand up standards compliant UTM services and be latest regulations on UTM / U-Space in the EU and other jurisdictions. Specifically, it gives you:

- an open source Remote ID "service provider" compatible with ASTM Remote ID standard
- an open source implementation of the ASTM USS <-> USS standard and compatible with the EU U-Space regulation for flight authorisation
- ability to consume geo-fences per the ED-269 standard
- a flight traffic feed aggregator that has different modules that can process and relay data around flights and airspace: geo-fence, flight declarations, air-traffic data.

There are different modules that enable this:

- _DSS Connectivity_: There are modules to connect and read for e.g. Remote ID data from a DSS, Strategic deconfliction / flight authorization
- _Flight Tracking_: It takes in flight tracking feeds from various sources e.g. ADS-B, live telemetry, Broadcast Remote ID and others and outputs as a single fused JSON feed and submits it to a Display Application e.g. [Flight Spotlight](https://github.com/openskies-sh/flight-spotlight) to be shown in real-time on a display
- _Geofence_: A Geofence can be submitted into Flight Blender and consequently transmitted to Spotlight
- _Flight Declaration_: Future flights up-to 24 hours can be submitted, this support both the ASTM USS <-> USS API and can also be used as a standalone component, for supported DSS APIs see below

## ▶️ Get started in 20 mins
Follow our 5-step process to deploy Flight Blender and Flight Spotlight and get started with the basic concepts of the software.

Read the ⏲️ [20-minute quickstart](deployment_support/README.md) now!

## Join the OpenUTM community

Join our Discord community via [this link](https://discord.gg/dnRxpZdd9a) 💫

## Openskies stack

To visualize flight tracking data you can use a complementary appplication like [Flight Spotlight](https://github.com/openskies-sh/flight-spotlight). To submit data like Geofences etc. into Flight Blender beyond the API you can use the user interface provided by Spotlight, for more information see the diagram below.

![OpenskiesStack](images/openskies-stack.png)


## Technical details

- To begin, review the [API Specification](http://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/openskies-sh/flight-blender/master/api/flight-blender-1.0.0-resolved.yaml) to understand the endpoints and the kind of data that you can set in Flight Blender.
- Then take a look at some data formats: [Flight tracking data](https://github.com/openskies-sh/flight-blender/blob/master/importers/air_traffic_samples/micro_flight_data_single.json). This file follows the format as specified in the [Air-traffic data protocol](https://github.com/openskies-sh/airtraffic-data-protocol-development/blob/master/Airtraffic-Data-Protocol.md)

## Submitting AOI, Flight Declarations and Geofence data

Take a look at sample data below to see the kind of data that can be submitted in Flight Blender

- [Area of Interest](https://github.com/openskies-sh/flight-blender/blob/master/importers/aoi_geo_fence_samples/aoi.geojson) as a GeoJSON
- [Geofence](https://github.com/openskies-sh/flight-blender/blob/master/importers/aoi_geo_fence_samples/geo_fence.geojson) as a GeoJSON, we have converters to convert EuroCAE from ED-269 standard
- [Flight Declaration](https://github.com/openskies-sh/flight-blender/blob/master/importers/flight_declarations_samples/flight-1.json). This file follows the format specified in [Flight Declaration Protocol](https://github.com/openskies-sh/flight-declaration-protocol-development), optionally when using DSS components it supports "operational intent" APIs.

## Running with Makefile

### Building and running the container
- **make build** will build the container.
- **make rebuild** will build the container by scratch
- **make up** will spin up the container in detached mode
- **make down** will stop the running container

### Running Code formatting
- **make lint** will check for coding practices/standards violations and apply fixes when possible.
- **make black** will format the black spaces between coding lines
- **make cleanimport** will remove unused imports and sort them in a more readable order

### Runnning tests
- **make test** will install the test dependancies to the container and execute all avaialble tests. (The container has to be up and running!)
-  This will also create a code coverage report in *htmlcov* directory.
- Browse the */flight-blender/htmlcov/index.html* to see the detailed tests coverage.

### Test Implementation
- Unit tests are implemented using [pytest test framework](https://docs.pytest.org/en/7.4.x/), and Django rest framework's test module.
- Inside each View module, a *test_views.py* is created for testing the routes exposed by *views.py*


## Image Credit

<a href="https://www.vecteezy.com/free-vector/blender">Blender Vectors by Vecteezy</a>
