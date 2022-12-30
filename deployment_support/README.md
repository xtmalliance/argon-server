# Introduction and objective
In this article you will understand how to deploy the OpenUTM system and the associated data flow. There are really three pieces of software that required: 
- Flight Blender (Backend)
- Flight Spotlight (Frontend - optional)
- Flight Passporit (Authorization server)

## Overview
![openutm-flow](images/openutm-data-flow.png)

### Setting up authorization server 
The OpenUTM system is a standards compliant 

### Creating a .env file 
When you deploy Blender you will need a environment file. The envinroment file can be requested via [our contact form](https://www.openskies.sh/#contact).

The section below deatils the environment file variables and a short comment on where they are used. 

## __1__
*Used to upload data into Flight Blender*, see `importers` directory in Flight Blender for more information. A JWT Bearer Token is needed to write any data into Flight Blender, this set of environment variables enable you t 

| Variable Key | Description |
|--------------|:-----:|

| BLENDER_WRITE_CLIENT_ID | The client credentials ID set in Flight Passport |
| BLENDER_WRITE_CLIENT_SECRET |  - |
| BLENDER_AUDIENCE |  - |
| BLENDER_WRITE_SCOPE |  - |
| BLENDER_AUDIENCE |  - |


## __2__
*Used in Flight Spotlight*

| Variable Key | Description |
|--------------|:-----:|
| PASSPORT_WEB_CLIENT_ID |  - |
| PASSPORT_WEB_CLIENT_SECRET|  - |
| OIDC_DOMAIN |  - |
| CALLBACK_URL |  - |


## __3__
*Used in Flight Spotlight*

| Variable Key | Description |
|--------------|:-----:|
| BING_KEY |  - |
| MAPBOX_KEY|  - |
| MAPBOX_ID |  - |

## __4__

| Variable Key | Description |
|--------------|:-----:|
| REDIS_URL |  - |
| TILE38_SERVER|  - |
| TILE38_PORT |  - |
| DEFAULT_APPROVED |  - |

## __5__
*Used in Flight Blender*


| Variable Key | Description |
|--------------|:-----:|
| DSS_SELF_AUDIENCE |  - |
| AUTH_DSS_CLIENT_ID|  - |
| AUTH_DSS_CLIENT_SECRET |  - |
| DSS_BASE_URL |  - |
| DSS_AUTH_TOKEN_ENDPOINT |  - |
| DSS_AUTH_JWKS_ENDPOINT |  - |
| BLENDER_FQDN |  - |

## __6__
*Used in Flight Blender*, these are the key backend services that are used in Blender

| Variable Key | Description |
|--------------|:-----:|
| REDIS_HOST | Location of the Redis instance e.g. redis if using Docker Compose |
| REDIS_PORT| 6379, if you using default / Docker compose, see also `redis.conf` file for changing this. |
| REDIS_BROKER_URL | This is used in Django to manage the Celery / task management processes if you are usnig  |
| HEARTBEAT_RATE_SECS |  - |
| OPENSKY_NETWORK_USERNAME |  - |
| OPENSKY_NETWORK_PASSWORD |  - |

### Running Flight Blender
You can run Blender by running `docker compose up` and then go to `http://localhost:8000`