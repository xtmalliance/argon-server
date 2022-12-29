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

The section below deatils the environment file variables. 


### Running Flight Blender
You can run Blender by running `docker compose up` and then go to `http://localhost:8000`