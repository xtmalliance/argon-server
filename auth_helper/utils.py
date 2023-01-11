

from django.http import JsonResponse
from functools import wraps
from django.contrib.auth import authenticate
import jwt
import json
import requests
from os import environ as env
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

def jwt_get_username_from_payload_handler(payload):
    username = payload.get('sub').replace('|', '.')
    authenticate(remote_user=username)
    return username

def requires_scopes(required_scopes):
    """Determines if the required scope is present in the access token
    Args:
        required_scopes (list): The scopes required to access the resource
    """
    
    s = requests.Session()
    def require_scope(f):
        @wraps(f)
        def decorated(*args, **kwargs):       
        
            request = args[0]
            auth = request.META.get("HTTP_AUTHORIZATION", None)        
            
            if auth:
                parts = auth.split()
                token = parts[1]            
            else:             
                response = JsonResponse({'detail': 'Authentication credentials were not provided'})
                response.status_code = 401
                return response
            
            API_IDENTIFIER = env.get('PASSPORT_AUDIENCE')
            try:
                unverified_token_headers = jwt.get_unverified_header(token)            
            except jwt.exceptions.DecodeError as de: 
                
                response = JsonResponse({'detail': 'Bearer token could not be decoded properly'})
                response.status_code = 401
                return response
            

            if 'kid' in unverified_token_headers:                   
                PASSPORT_URL = '{}/.well-known/jwks.json'.format(env.get('PASSPORT_URL','http://local.test:9000'))     
                jwks_data = s.get(PASSPORT_URL).json()                 
                jwks = jwks_data
                public_keys = {}                
                for jwk in jwks['keys']:
                    kid = jwk['kid']
                    public_keys[kid] = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
                try:
                    kid = unverified_token_headers['kid']                    
                except (KeyError, ValueError) as ve:         
                    response = JsonResponse({'detail': 'Invalid public key details in token / token cannot be verified'})
                    response.status_code = 401
                    return response
                else:     
                    try:               
                        assert kid in public_keys
                    except AssertionError as ae:
                        response = JsonResponse({'detail': 'Invalid public key details in token / token cannot be verified'})
                        response.status_code = 401
                        return response
                    else:
                        public_key = public_keys[kid]
                    
                                    
                try:
                    decoded = jwt.decode(token, public_key, audience=API_IDENTIFIER, algorithms=['RS256'])                    
                except jwt.ImmatureSignatureError as es: 
                    response = JsonResponse({'detail': 'Token Signature has is not valid'})
                    response.status_code = 401
                    return response
                except jwt.ExpiredSignatureError as es: 
                    response = JsonResponse({'detail': 'Token Signature has expired'})
                    response.status_code = 401
                    return response
                except jwt.InvalidAudienceError as es: 
                    response = JsonResponse({'detail': 'Invalid audience in token'})
                    response.status_code = 401
                    return response                
                except jwt.InvalidIssuerError as es: 
                    response = JsonResponse({'detail': 'Invalid issuer for token'})
                    response.status_code = 401
                    return response
                except jwt.InvalidSignatureError as es:                     
                    response = JsonResponse({'detail': 'Invalid signature in token'})
                    response.status_code = 401
                    return response
                except jwt.DecodeError as es: 
                    response = JsonResponse({'detail': 'Token canot be decoded'})
                    response.status_code = 401
                    return response
                except Exception as e: 
                    response = JsonResponse({'detail': 'Invalid token'})
                    response.status_code = 401
                    return response                

                if decoded.get("scope"):
                    token_scopes = decoded["scope"].split()
                    token_scopes_set = set(token_scopes)   
                    if set(required_scopes).issubset(token_scopes_set):
                        return f(*args, **kwargs)
                response = JsonResponse({'message': 'You don\'t have access to this resource'})
                response.status_code = 403
                return response

            else:                
                # This is for testing DSS locally
                token_details = jwt.decode(token,algorithms=['RS256'], options={"verify_signature": False})        

                if 'iss' in token_details.keys() and token_details['iss'] in  ['dummy','NoAuth']:          
                    return f(*args, **kwargs)
                else:
                    response = JsonResponse({'detail': 'Invalid token provided'})
                    response.status_code = 401                    
                    return response

        return decorated

    return require_scope


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token
    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r