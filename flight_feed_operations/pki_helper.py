from .models import SignedTelmetryPublicKey
from http_message_signatures import HTTPMessageSigner, HTTPMessageVerifier, HTTPSignatureKeyResolver, algorithms
import requests, base64, hashlib, http_sfv

import jwt
import json
import requests
import logging
from auth_helper.common import get_redis
logger = logging.getLogger('django')

class MyHTTPSignatureKeyResolver(HTTPSignatureKeyResolver):
    def __init__(self, known_kids):
        self.known_kids = known_kids
    def resolve_public_key(self, key_id: str):        
        if key_id in self.known_kids.keys():
            return self.known_kids[key_id]
            


class MessageVerifier():
    def get_public_keys(self):
        r = get_redis()
        public_keys = {}       
        s = requests.Session()
        all_public_keys = SignedTelmetryPublicKey.objects.filter(is_active = 1)
        for current_public_key in all_public_keys:
            redis_jwks_key = current_public_key.id + '-jwks'
            current_kid = current_public_key.key_id
            if r.exists(redis_jwks_key):
                k = r.get(redis_jwks_key)
                key = json.loads(k)
            else:                
                jwks_data = s.get(current_public_key).json() 
                jwk = next((item for item in jwks_data['keys'] if item['kid'] == current_kid), None)                   
                if jwk: 
                    key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))              
                else: 
                    key = '000'
                r.set(redis_jwks_key, json.dumps(key))
            public_keys[current_kid] = key

    def verify_message(self, request) -> bool:
        verifier = HTTPMessageVerifier(signature_algorithm=algorithms.HMAC_SHA256, key_resolver=MyHTTPSignatureKeyResolver())
        verified = verifier.verify(request)

        return verified

