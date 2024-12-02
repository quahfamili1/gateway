from jose import jwt
import requests
from app.config import settings

class KeycloakAuth:
    def __init__(self, well_known_url: str = settings.KEYCLOAK_WELL_KNOWN_URL):
        self.well_known_url = well_known_url
        self.jwks_url = f"{well_known_url}/protocol/openid-connect/certs"
        self.token_info = {}

    def decode_token(self, token: str):
        try:
            jwks = requests.get(self.jwks_url).json()
            header = jwt.get_unverified_header(token)
            key = next(k for k in jwks["keys"] if k["kid"] == header["kid"])
            self.token_info = jwt.decode(token, key, algorithms=["RS256"], audience=settings.OIDC_CLIENT_ID)
            return self.token_info
        except Exception as e:
            raise ValueError(f"Token decoding failed: {e}")

    def get_user_info(self):
        return {
            "email": self.token_info.get("email"),
            "preferred_username": self.token_info.get("preferred_username"),
            "groups": self.token_info.get("groups", []),
        }
