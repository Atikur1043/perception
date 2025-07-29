from pydantic import BaseModel

class Token(BaseModel):
    """
    Pydantic model for the JWT access token response.
    """
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """
    Pydantic model for the data encoded within the JWT.
    """
    email: str | None = None
