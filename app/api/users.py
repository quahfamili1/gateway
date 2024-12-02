from fastapi import APIRouter, HTTPException
import requests
import logging
from app.auth import KeycloakAuth
from app.config import settings

router = APIRouter()

logger = logging.getLogger(__name__)

OPENMETADATA_API_URL = settings.OPENMETADATA_API_URL

def get_headers():
    """Retrieve authorization headers for OpenMetadata API."""
    if not settings.OPENMETADATA_TOKEN:
        logger.error("OpenMetadata API token not configured.")
        raise HTTPException(status_code=500, detail="OpenMetadata API token is not configured")
    return {"Authorization": f"Bearer {settings.OPENMETADATA_TOKEN}", "Content-Type": "application/json"}

@router.post("/register")
def register_user(token: str):
    """Decode Keycloak token and register user in OpenMetadata."""
    try:
        headers = get_headers()
        user_info = KeycloakAuth().decode_token(token)
        user_data = KeycloakAuth().get_user_info()

        # Check and create user in OpenMetadata
        user_payload = {"name": user_data["email"], "email": user_data["email"], "teams": []}
        response = requests.post(f"{OPENMETADATA_API_URL}/users", json=user_payload, headers=headers)
        response.raise_for_status()

        # Check and create group in OpenMetadata
        for group in user_data["groups"]:
            group_response = requests.get(f"{OPENMETADATA_API_URL}/teams?name={group}", headers=headers)
            if group_response.status_code == 404:
                group_payload = {"name": group}
                requests.post(f"{OPENMETADATA_API_URL}/teams", json=group_payload, headers=headers)

        return {"message": "User registered and assigned to groups successfully."}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
