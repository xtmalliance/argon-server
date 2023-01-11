
import datetime
from typing import Dict, List, Optional
import urllib.parse
import uuid

import jwcrypto.common
import jwcrypto.jwk
import jwcrypto.jws
import jwcrypto.jwt
import jwt
import requests

ALL_SCOPES = [
    "dss.write.identification_service_areas",
    "dss.read.identification_service_areas",
    "utm.strategic_coordination",
    "utm.constraint_management",
    "utm.constraint_consumption",
]

EPOCH = datetime.datetime.utcfromtimestamp(0)
TOKEN_REFRESH_MARGIN = datetime.timedelta(seconds=15)
CLIENT_TIMEOUT = 60  # seconds


class AuthAdapter(object):
    """Base class for an adapter that add JWTs to requests."""

    def __init__(self):
        self._tokens = {}

    def issue_token(self, intended_audience: str, scopes: List[str]) -> str:
        """Subclasses must return a bearer token for the given audience."""

        raise NotImplementedError()

    def get_headers(self, url: str, scopes: List[str] = None) -> Dict[str, str]:
        if scopes is None:
            scopes = ALL_SCOPES
        intended_audience = urllib.parse.urlparse(url).hostname
        scope_string = " ".join(scopes)
        if intended_audience not in self._tokens:
            self._tokens[intended_audience] = {}
        if scope_string not in self._tokens[intended_audience]:
            token = self.issue_token(intended_audience, scopes)
        else:
            token = self._tokens[intended_audience][scope_string]
        payload = jwt.decode(token, options={"verify_signature": False})
        expires = EPOCH + datetime.timedelta(seconds=payload["exp"])
        if datetime.datetime.utcnow() > expires - TOKEN_REFRESH_MARGIN:
            token = self.issue_token(intended_audience, scopes)
        self._tokens[intended_audience][scope_string] = token
        return {"Authorization": "Bearer " + token}

    def add_headers(self, request: requests.PreparedRequest, scopes: List[str]):
        for k, v in self.get_headers(request.url, scopes).items():
            request.headers[k] = v

    def get_sub(self) -> Optional[str]:
        """Retrieve `sub` claim from one of the existing tokens"""
        for _, tokens_by_scope in self._tokens.items():
            for token in tokens_by_scope.values():
                payload = jwt.decode(token, options={"verify_signature": False})
                if "sub" in payload:
                    return payload["sub"]
        return None




class NoAuth(AuthAdapter):
    """Auth adapter that generates tokens without an auth server.
    While no server is used, the access tokens generated are fully valid and their
    signatures will validate against test-certs/auth2.pem.
    """

    # This is the private key from test-certs/auth2.key.
    dummy_private_key = jwcrypto.jwk.JWK.from_pem(
        "-----BEGIN RSA PRIVATE KEY-----\n"
        "MIICWwIBAAKBgHkNtpy3GB0YTCl2VCCd22i0rJwIGBSazD4QRKvH6rch0IP4igb+\n"
        "02r7t0X//tuj0VbwtJz3cEICP8OGSqrdTSCGj5Y03Oa2gPkx/0c0V8D0eSXS/CUC\n"
        "0qrYHnAGLqko7eW87HW0rh7nnl2bB4Lu+R8fOmQt5frCJ5eTkzwK5YczAgMBAAEC\n"
        "gYAtSgMjGKEt6XQ9IucQmN6Iiuf1LFYOB2gYZC+88PuQblc7uJWzTk08vlXwG3l3\n"
        "JQ/h7gY0n6JhH8RJW4m96TO8TrlHLx5aVcW8E//CtgayMn3vBgXida3wvIlAXT8G\n"
        "WezsNsWorXLVmz5yov0glu+TIk31iWB5DMs4xXhXdH/t8QJBALQzvF+y5bZEhZin\n"
        "qTXkiKqMsKsJbXjP1Sp/3t52VnYVfbxN3CCb7yDU9kg5QwNa3ungE3cXXNMUr067\n"
        "9zIraekCQQCr+NSeWAXIEutWewPIykYMQilVtiJH4oFfoEpxvecVv7ulw6kM+Jsb\n"
        "o6Pi7x86tMVkwOCzZzy/Uyo/gSHnEZq7AkEAm0hBuU2VuTzOyr8fhvtJ8X2O97QG\n"
        "C6c8j4Tk7lqXIuZeFRga6la091vMZmxBnPB/SpX28BbHvHUEpBpBZ5AVkQJAX7Lq\n"
        "7urg3MPafpeaNYSKkovG4NGoJgSgJgzXIJCjJfE6hTZqvrMh7bGUo9aZtFugdT74\n"
        "TB2pKncnTYuYyDN9vQJACDVr+wvYYA2VdnA9k+/1IyGc1HHd2npQqY9EduCeOGO8\n"
        "rXQedG6rirVOF6ypkefIayc3usipVvfadpqcS5ERhw==\n"
        "-----END RSA PRIVATE KEY-----".encode("UTF-8")
    )

    EXPIRATION = 3600  # seconds

    def __init__(self, sub: str = "uss_noauth"):
        super().__init__()
        self.sub = sub

    # Overrides method in AuthAdapter
    def issue_token(self, intended_audience: str, scopes: List[str]) -> str:
        timestamp = int((datetime.datetime.utcnow() - EPOCH).total_seconds())
        jwt = jwcrypto.jwt.JWT(
            header={"typ": "JWT", "alg": "RS256"},
            claims={
                "sub": self.sub,
                "client_id": self.sub,
                "scope": " ".join(scopes),
                "aud": intended_audience,
                "nbf": timestamp - 1,
                "exp": timestamp + NoAuth.EXPIRATION,
                "iss": "NoAuth",
                "jti": str(uuid.uuid4()),
            },
            algs=["RS256"],
        )
        jwt.make_signed_token(NoAuth.dummy_private_key)
        return jwt.serialize()
