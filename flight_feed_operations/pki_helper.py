from .models import SignedTelmetryPublicKey
from http_message_signatures import HTTPMessageSigner, HTTPMessageVerifier, HTTPSignatureKeyResolver, algorithms
import requests
from http_message_signatures.exceptions import InvalidSignature
import jwt
import json
import requests
import logging
from auth_helper.common import get_redis
logger = logging.getLogger('django')

class MyHTTPSignatureKeyResolver(HTTPSignatureKeyResolver):
    def __init__(self, jwk):
        self.jwk = jwk
    def resolve_public_key(self, key_id = None):    
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(self.jwk)
        return public_key
            

class MessageVerifier():
    def get_public_keys(self):
        r = get_redis()
        public_keys = {}       
        s = requests.Session()
        all_public_keys = SignedTelmetryPublicKey.objects.filter(is_active = 1)
        for current_public_key in all_public_keys:
            redis_jwks_key = str(current_public_key.id) + '-jwks'
            current_kid = current_public_key.key_id
            if r.exists(redis_jwks_key):
                k = r.get(redis_jwks_key)
                key = json.loads(k)
            else:                                
                response = s.get(current_public_key.url)                
                jwks_data = response.json()
                if 'keys' in jwks_data:                
                    jwk = next((item for item in jwks_data['keys'] if item['kid'] == current_kid), None)                   
                else: 
                    if 'kid' in jwks_data.keys():
                        jwk = jwks_data if current_kid == jwks_data['kid'] else None
                    else: 
                        jwk = None
                key = jwk if jwk else {'000'}
              
                r.set(redis_jwks_key, json.dumps(key))
                r.expire(redis_jwks_key, 60000)
            public_keys[current_kid] = key
        return public_keys

    def verify_message(self, request) -> bool:
        stored_public_keys=  self.get_public_keys()
        
        if bool(stored_public_keys):       
            r = requests.Request("PUT", request.build_absolute_uri(), json=request.data, headers=request.headers)
        
            for key_id, jwk in stored_public_keys.items():  
                verifier = HTTPMessageVerifier(signature_algorithm = algorithms.RSA_PSS_SHA512, key_resolver = MyHTTPSignatureKeyResolver(jwk= jwk))                
                verifier.verify(r)
                # try: 
                # verifier.verify(request)
                # except InvalidSignature as i_sig:
                    # logger.error(i_sig)
                    # return False

            return True
        else:
            return False

