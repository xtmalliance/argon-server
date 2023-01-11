# Introduction and objective
In this article you will understand how to deploy the Flight Blender backend / data processsing engine. If you need a front end / display you will need to install Flight Spotlight (which communicates with Blender via the API) and finally for production we also recommend that you use Flight Passport.

## 15-min Quickstart 

In this document, we will setup, this is for local development / testing only, for a more detailed "Production" instance see (oauth_infrastructure)[oauth_infrastructure.md] document, you will need a full fledged OAUTH server like [Flight Passport](https://github.com/openskies-sh/flight_passport), for this quickstart we will use the simple authentication / token generation mechanism that requires not additional server setup. Specifically we will: 

1. Create a .env file 
2. Use Docker compose to run Flight Blender
3. Use the importers to submit some flight information 
4. Finally query the flight data using the API via a tool like Postman. 

### 1. Create .env File

For this quick start we will use the [sample .env](../.env.sample) file. You can copy the file to create a new .env file, we will go over the .env file below. 

| Variable Key | Data Type | Description |
|--------------|--------------|:-----:|
| SECRET_KEY | string |This is used in Django, it is recommended that you use a long SECRET Key as string here |
| IS_DEBUG |integer | Set this as 0 if you are using it locally |
| ALLOWED_HOSTS | string | This is used in Django, it is recommended that if you are not using IS_DEBUG above, then this needs to be set as a the domain name, if you are using IS_DEBUG above, then the system automatically allows all hosts|
| REDIS_HOST | string | Blender uses Redis as the backend, you can use localhost if you are running redis locally |
| REDIS_PORT | integer | Normally Redis runs at port 6379, you can set it here, if you dont setup the REDIS Host and Port, Blender will use the default values |
| REDI_PASSWORD | string | In production the Redis instance is password protected, set the password here, see redis.conf for more information |
| REDIS_BROKER_URL | string | Blender has background jobs controlled via Redies, you can setup the Broker URL here |
| HEARTBEAT_RATE_SECS |integer | Generally set it to 1 or 2 seconds, this is used when querying data externally to other USSPs |
| DSS_SELF_AUDIENCE |string | This is the domain name of the lender instance you can set it as localhost or development / testing |
| AUTH_DSS_CLIENT_ID | string | (optional) Sometimes authorities will provide special tokens for accessing the DSS, if you are using it locally via `/build/dev/run_locally.sh` via the InterUSS /DSS repository, you can just use a random long string |
| AUTH_DSS_CLIENT_SECRET | string | (optional) Similar to above sometimes authorities provide  |
| DSS_BASE_URL | string | Set the URL for DSS if you are using it it can be something like `http://host.docker.internal:8082/` if you are using the InterUSS / DSS build locally stack. |
| POSTGRES_USER | string | Set the user for the Blender Database |
| POSTGRES_PASSWORD| string | Set a strong password for accessing PG in Docker |
| POSTGRES_DB | string| You can name a appropriate name, see the sample file |
| POSTGRES_HOST | string| You can name a appropriate name, see the sample file |
| PGDATA | string | This is where the data is stored, you can use `/var/lib/postgresql/data/pgdata` here |


### 2. Use Docker Compose to stand up Flight Blender 
Once you have created and saved a .env file you than use the [docker-compose.yaml](../docker-compose.yml) file to start the instance. Just run `docker compose up` and a running instance of Flight Blender will be avaialable. 

#### Running Flight Blender
You can run Blender by running `docker compose up` and then go to `http://localhost:8000`, Congratulations 🎉 we now have a running version of the system!

### 3. Upload some flight information
The [importers](../importers/) directory has a set of scripts that help you with uploading some data / flight tracks. We will use the [import_flight_json_blender_local.py](../importers/import_flight_json_blender_local.py) script here. You will have to setup a environment like Anaconda or simiular and install dependencies via something like `pip install -r requirements.txt` then you can run the import script via `python import_flight_json_blender_local.py` this will send some observations to the `/set_air_traffic` POST endpoint. This script will send a observation and then wait for 10 seconds and send another one. 

### 4. Use Postman to query the API
While the script is running you can install Postman and which should help us query ther API. You can import the [Postman Collection](../api/flight_blender_api.postman_collection.json) prior. You will also need a "NoAuth" Bearer JWT token that you can generate by using the [get_access_token.py](../importers/get_access_token.py) script. You should have a scope of `blender.read` and a audience of `testflight.flightblender.com`. We will use this token to go to the Postman collection > Flight Feed Operations > Get airtraffic observations. You should be able to see output of the flight feed. 
