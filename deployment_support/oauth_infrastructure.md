# Introduction and objective
In this article you will understand how to deploy the OpenUTM system and the associated data flow. There are really three pieces of software that required:
- Flight Blender (Backend)
- Flight Spotlight (Frontend - optional)
- Flight Passport (Authorization server)

## Overview
![openutm-flow](images/openutm-data-flow.png)

## Quickstart

In this document, we will setup
- Flight Blender via Docker and then
- use the importers to submit some flight information
- and finally query the flight data using the API via a tool like Postman.

Flight Blender follows the ASTM standards for access and authorization.


## Detailed Instructions

### Setting up authorization server
The OpenUTM system is a standards compliant system and requires a OAUTH server for managing Identity and Authorization, the ASTM standard requires that JWT tokens be used to access UTM services, JWT tokens can be issued by any server, we recommend using Flight Passport since it gives full authorization capabilities.

### Creating a .env file
When you deploy Blender you will need a environment file. The environment file can be requested via [our contact form](https://www.openskies.sh/#contact).

The section below details the environment file variables and a short comment on where they are used.

## __1__
*Used to upload data into Flight Blender*, see `importers` directory in Flight Blender for more information. A JWT Bearer Token is needed to write any data into Flight Blender, this set of environment variables enable you to write data into Flight Blender.

| Variable Key | Description |
|--------------|:-----:|

| BLENDER_WRITE_CLIENT_ID | The client credentials ID set in Flight Passport |
| BLENDER_WRITE_CLIENT_SECRET | - |
| BLENDER_AUDIENCE | - |
| BLENDER_WRITE_SCOPE | - |
| BLENDER_AUDIENCE | - |

## __2__
*Used in Flight Spotlight*, these settings are used in the Spotlight to enable login into the system. Client ID and Client Secret are standard

| Variable Key | Description |
|--------------|:-----:|
| PASSPORT_WEB_CLIENT_ID | - |
| PASSPORT_WEB_CLIENT_SECRET| - |
| OIDC_DOMAIN | - |
| CALLBACK_URL | - |

## __3__
*Used in Flight Spotlight*, these variables are used in Spotlight for basemaps as XYZ tiles.

| Variable Key | Description |
|--------------|:-----:|
| BING_KEY | Get a key from Bing Portal |
| MAPBOX_KEY| - |
| MAPBOX_ID | - |

## __4__
*Used in Flight Spotlight*, these variables specify the backend servers for Spotlight to do data processing
| Variable Key | Description |
|--------------|:-----:|
| REDIS_URL | - |
| TILE38_SERVER| - |
| TILE38_PORT | - |
| DEFAULT_APPROVED | - |

## __5__
*Used in Flight Blender*, these variables are used in Flight Blender to ensure DSS connectivity and interoperability ith other

| Variable Key | Description |
|--------------|:-----:|
| DSS_SELF_AUDIENCE | - |
| AUTH_DSS_CLIENT_ID| - |
| AUTH_DSS_CLIENT_SECRET | - |
| DSS_BASE_URL | - |
| DSS_AUTH_TOKEN_ENDPOINT | - |
| DSS_AUTH_JWKS_ENDPOINT | - |
| BLENDER_FQDN | - |

## __6__
*Used in Flight Blender*, these are the key backend services that are used in Blender

| Variable Key | Description |
|--------------|:-----:|
| REDIS_HOST | Location of the Redis instance e.g. redis if using Docker Compose |
| REDIS_PORT| 6379, if you using default / Docker compose, see also `redis.conf` file for changing this. |
| REDIS_BROKER_URL | This is used in Django to manage the Celery / task management processes if you are using it  |
| HEARTBEAT_RATE_SECS | This is the refresh rate of the system, normally set to 1 or 2 seconds |
| OPENSKY_NETWORK_USERNAME | Get a Username from https://opensky-network.org/ |
| OPENSKY_NETWORK_PASSWORD | - |

USING_DOCKER_COMPOSE| Set this variable to use Docker Compose |
DATABASE_URL| Set the URL of the Database so Docker compose can pick up the db, by default SQLite is the database. e.g. psql://mydatabaseuser:mypasswordd@myproject_db:5432/myproject_db |


For Advanced operations, the following two configurations are recommended:

| Variable Key | Data Type | Description |
|--------------|--------------|:-----:|
| AMQP_URL |string | (Optional) A full connection url to a AMQP server, when this is set, messages related to your operations are sent to it, your clients can subscribe to them. |
| ENABLE_CONFORMANCE_MONITORING | int | (Optional) By default conformance monitoring is turned off, set this flag if you want to enable conformance monitoring. Conformance monitoring is a advanced UTM service so it is recommended that this service be turned off initially. |


### Running Flight Blender
You can run Blender by running `docker compose up` and then go to `http://localhost:8000`
