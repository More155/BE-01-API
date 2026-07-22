import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from supabase import Client, create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="Auth Practice API")
security = HTTPBearer()


class Credentials(BaseModel):
    email: str
    password: str


@app.post("/auth/signup", status_code=201)
def signup(creds: Credentials):
    try:
        result = supabase.auth.sign_up({"email": creds.email, "password": creds.password})
        return {"user": result.user}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/login")
def login(creds: Credentials):
    try:
        result = supabase.auth.sign_in_with_password(
            {"email": creds.email, "password": creds.password}
        )
        return {
            "access_token": result.session.access_token,
            "refresh_token": result.session.refresh_token,
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid login credentials")


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        user = supabase.auth.get_user(token)
        return user.user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@app.post("/auth/logout", status_code=204)
def logout(user=Depends(get_current_user)):
    supabase.auth.sign_out()


@app.get("/protected/profile")
def profile(user=Depends(get_current_user)):
    return {"id": user.id, "email": user.email}


@app.get("/public/info")
def public_info():
    return {"message": "Welcome stranger! This info is public."}
