from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
from dotenv import load_dotenv
import logging

# Load environment variables explicitly
load_dotenv()

class Settings(BaseSettings):
    # Keycloak Configuration
    OIDC_CLIENT_ID: str = Field(..., env="OIDC_CLIENT_ID")
    OIDC_CLIENT_SECRET: str = Field(..., env="OIDC_CLIENT_SECRET")
    KEYCLOAK_WELL_KNOWN_URL: str = Field(..., env="KEYCLOAK_WELL_KNOWN_URL")

    # OpenMetadata Configuration
    OPENMETADATA_API_URL: str = Field(..., env="OPENMETADATA_API_URL")
    OPENMETADATA_TOKEN: str = Field(..., env="OPENMETADATA_TOKEN")

    # JWT Configuration
    TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="TOKEN_EXPIRE_MINUTES")  # Ensure it's an integer

    # CORS Configuration
    CORS_ORIGINS: str = Field(default="*", env="CORS_ORIGINS")

    # Debug and Logging
    DEBUG: bool = Field(default=False, env="DEBUG")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def get_cors_origins(self) -> List[str]:
        """Parse CORS_ORIGINS environment variable into a list."""
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS


# Initialize settings instance
settings = Settings()

# Add logging to confirm settings loaded properly
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.debug(f"Loaded OpenMetadata API URL: {settings.OPENMETADATA_API_URL}")
logger.debug(f"Loaded Keycloak Well-Known URL: {settings.KEYCLOAK_WELL_KNOWN_URL}")
logger.debug(f"Loaded Keycloak Client ID: {settings.OIDC_CLIENT_ID}")
logger.debug(f"Token Expiration Minutes: {settings.TOKEN_EXPIRE_MINUTES}")  # Log this value for verification
logger.debug(f"Debug Mode: {settings.DEBUG}")
logger.debug(f"CORS Origins: {settings.get_cors_origins()}")
