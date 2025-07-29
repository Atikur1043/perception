import secrets
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

# Import Google's libraries for verification
from google.oauth2 import id_token
from google.auth.transport import requests

from app.db.database import User
from app.models.user_models import UserCreate, UserOut
from app.models.token_models import Token
from app.models.google_auth_models import GoogleCredential
from app.services.auth_service import get_password_hash, verify_password, create_access_token
from app.services.auth_dependencies import get_current_user
from app.core.config import settings

router = APIRouter()

@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(user_in: UserCreate):
    if await User.find_one(User.email == user_in.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    if await User.find_one(User.username == user_in.username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username is already taken")
    
    hashed_password = get_password_hash(user_in.password)
    
    new_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_password,
        role=user_in.role
    )
    await new_user.insert()
    return new_user

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await User.find_one({"$or": [{"email": form_data.username}, {"username": form_data.username}]})
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/google", response_model=Token)
async def login_with_google(cred: GoogleCredential):
    try:
        idinfo = id_token.verify_oauth2_token(
            cred.credential, requests.Request(), settings.GOOGLE_CLIENT_ID
        )
        email = idinfo.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Email not found in Google token")

        user = await User.find_one(User.email == email)

        if not user:
            # --- IMPROVED USERNAME LOGIC ---
            # 1. Get the user's name from the Google token
            name = idinfo.get("name")
            
            # 2. Create a base username from the name (e.g., "John Smith" -> "johnsmith")
            #    or fall back to the email prefix if the name is not available.
            if name:
                base_username = name
            else:
                base_username = email.split('@')[0]

            # 3. Ensure the username is unique
            username = base_username
            while await User.find_one(User.username == username):
                # If the username is taken, append a short random string
                username = base_username + secrets.token_hex(2)
            # --- END OF IMPROVED LOGIC ---

            new_user = User(
                username=username,
                email=email,
                hashed_password=get_password_hash(secrets.token_urlsafe(16)),
                role="student"
            )
            await new_user.insert()
            user = new_user

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
        
        return {"access_token": access_token, "token_type": "bearer"}

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate Google credentials",
        )

@router.get("/users/me", response_model=UserOut)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get the details of the currently authenticated user.
    """
    return current_user
