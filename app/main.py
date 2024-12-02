from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from app.auth import KeycloakAuth
from app.config import settings
import requests
import logging

# Configure logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Keycloak Authentication Handler
auth_handler = KeycloakAuth(settings.KEYCLOAK_WELL_KNOWN_URL)

# OpenMetadata API URL
OPENMETADATA_API_URL = settings.OPENMETADATA_API_URL


def get_headers():
    """Retrieve authorization headers for OpenMetadata API."""
    if not settings.OPENMETADATA_TOKEN:
        logger.error("OpenMetadata API token not configured.")
        raise HTTPException(status_code=500, detail="OpenMetadata API token is not configured")
    return {"Authorization": f"Bearer {settings.OPENMETADATA_TOKEN}", "Content-Type": "application/json"}


@app.get("/")
async def root():
    """Redirect users to Keycloak for authentication."""
    try:
        keycloak_auth_url = (
            f"http://localhost:9000/realms/Data-sec/protocol/openid-connect/auth"
            f"?client_id={settings.OIDC_CLIENT_ID}"
            f"&redirect_uri=http://localhost:8005/callback"
            f"&response_type=code"
            f"&scope=openid email profile"
        )
        logger.debug(f"Constructed Keycloak auth URL: {keycloak_auth_url}")
        return RedirectResponse(url=keycloak_auth_url)
    except Exception as e:
        logger.error(f"Error generating Keycloak auth URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate Keycloak auth URL")


@app.get("/callback")
async def callback(code: str = Query(...)):
    """Handle Keycloak's callback and process the user."""
    try:
        logger.debug("Received callback with authorization code")
        # Exchange authorization code for token
        token_response = requests.post(
            f"{settings.KEYCLOAK_WELL_KNOWN_URL}/protocol/openid-connect/token",
            data={
                "grant_type": "authorization_code",
                "client_id": settings.OIDC_CLIENT_ID,
                "client_secret": settings.OIDC_CLIENT_SECRET,
                "redirect_uri": "http://localhost:8005/callback",
                "code": code,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if token_response.status_code != 200:
            logger.error(f"Failed to exchange code for token: {token_response.text}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to exchange code for token: {token_response.text}",
            )

        token_data = token_response.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=500, detail="Access token not received.")

        # Decode and validate the token
        user_info = auth_handler.decode_token(access_token)
        user_data = auth_handler.get_user_info()

        logger.debug(f"User Info: {user_data}")

        # Create or fetch user in OpenMetadata
        user_payload = {"name": user_data["email"], "email": user_data["email"], "teams": []}
        headers = get_headers()

        user_response = requests.post(f"{OPENMETADATA_API_URL}/users", json=user_payload, headers=headers)
        if user_response.status_code == 201:
            logger.info(f"User {user_data['email']} registered in OpenMetadata.")
        elif user_response.status_code == 409:
            logger.info(f"User {user_data['email']} already exists in OpenMetadata.")
        else:
            logger.error(f"Failed to register user: {user_response.text}")
            raise HTTPException(status_code=500, detail="User registration failed")

        # Redirect to OpenMetadata dashboard with the access token
        openmetadata_dashboard_url = f"http://localhost:8585/?token={access_token}"
        logger.debug(f"Redirecting to OpenMetadata: {openmetadata_dashboard_url}")
        return RedirectResponse(url=openmetadata_dashboard_url)

    except Exception as e:
        logger.error(f"Error during callback processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))
