import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from supabase import AuthApiError, Client, create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="Auth Practice API (rematch)")
security = HTTPBearer(auto_error=False)


class AuthError(HTTPException):
    pass


@app.exception_handler(AuthError)
async def auth_error_handler(request: Request, exc: AuthError):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


class Credentials(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None


@app.post("/auth/signup", status_code=201)
def signup(creds: Credentials):
    if not creds.email or not creds.password:
        return JSONResponse(status_code=400, content={"error": "email and password are required"})
    try:
        result = supabase.auth.sign_up({"email": creds.email, "password": creds.password})
    except AuthApiError as e:
        return JSONResponse(status_code=400, content={"error": e.message})
    return {"user": result.user}


@app.post("/auth/login")
def login(creds: Credentials):
    if not creds.email or not creds.password:
        return JSONResponse(status_code=400, content={"error": "email and password are required"})
    try:
        result = supabase.auth.sign_in_with_password(
            {"email": creds.email, "password": creds.password}
        )
    except AuthApiError:
        return JSONResponse(status_code=401, content={"error": "Invalid login credentials"})
    return {
        "access_token": result.session.access_token,
        "refresh_token": result.session.refresh_token,
    }


def get_bearer_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    if credentials is None or not credentials.credentials:
        raise AuthError(status_code=401, detail="Access token required")
    return credentials.credentials


def get_current_user(token: str = Depends(get_bearer_token)):
    try:
        user_response = supabase.auth.get_user(token)
    except AuthApiError:
        raise AuthError(status_code=401, detail="Invalid or expired token")
    if not user_response or not user_response.user:
        raise AuthError(status_code=401, detail="Invalid or expired token")
    return user_response.user


@app.post("/auth/logout", status_code=204)
def logout(user=Depends(get_current_user), token: str = Depends(get_bearer_token)):
    # Target the caller's own token explicitly (still only the anon key, not
    # service_role) instead of the shared client's cached session, which would
    # revoke whichever session happened to be cached under concurrent traffic.
    supabase.auth.admin.sign_out(token, "local")


@app.get("/protected/profile")
def profile(user=Depends(get_current_user)):
    return {"id": user.id, "email": user.email}


@app.get("/protected/dashboard")
def dashboard(user=Depends(get_current_user)):
    return {"message": f"Welcome to your dashboard, {user.email}"}


@app.get("/public/info")
def public_info():
    return {"message": "Welcome stranger! This info is public."}
