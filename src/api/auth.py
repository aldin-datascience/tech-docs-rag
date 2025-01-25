from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from project_config.logger import get_logger
from project_config.settings import API_USERNAME, API_PASSWORD  # Replace with the actual variable names in your .env

logger = get_logger(__name__, log_file="auth.log")

security = HTTPBasic()


def simple_auth(credentials: HTTPBasicCredentials = Depends(security)) -> bool:
    """
    Simple username/password authentication using Basic Auth.

    Compares credentials.username and credentials.password against the
    values stored in .env (exposed via src.project_config.settings).
    No hashing is used in this example.

    :param credentials: The HTTP Basic credentials (username, password).
    :return: True if authentication is successful, otherwise raises HTTPException.
    """
    logger.info("Attempting to authenticate user.")

    if credentials.username != API_USERNAME or credentials.password != API_PASSWORD:
        logger.warning("Authentication failed: Invalid credentials.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Basic"},
        )

    logger.info("Authentication successful.")
    return True
