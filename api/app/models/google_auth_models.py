from pydantic import BaseModel

class GoogleCredential(BaseModel):
    """
    Pydantic model for the credential received from the frontend
    after a successful Google login.
    """
    credential: str
