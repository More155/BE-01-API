from typing import Optional

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from supabase import AuthApiError

from auth_service import supabase

router = APIRouter()


def extract_bearer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


class AuthCredentials(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None


@router.post("/auth/signup", status_code=201)
def signup(payload: AuthCredentials):
    if not payload.email or not payload.password:
        return JSONResponse(status_code=400, content={"error": "email and password are required"})

    try:
        result = supabase.auth.sign_up({"email": payload.email, "password": payload.password})
    except AuthApiError as e:
        return JSONResponse(status_code=400, content={"error": e.message})

    user = result.user
    return {
        "id": user.id,
        "email": user.email,
        "created_at": user.created_at,
    }


@router.post("/auth/login")
def login(payload: AuthCredentials):
    if not payload.email or not payload.password:
        return JSONResponse(status_code=400, content={"error": "email and password are required"})

    try:
        result = supabase.auth.sign_in_with_password(
            {"email": payload.email, "password": payload.password}
        )
    except AuthApiError:
        return JSONResponse(status_code=401, content={"error": "Invalid login credentials"})

    return {
        "access_token": result.session.access_token,
        "refresh_token": result.session.refresh_token,
        "token_type": "bearer",
    }


@router.get("/public/info")
def public_info():
    return {"message": "Welcome stranger! This info is public."}


@router.get("/protected/profile")
def get_profile(authorization: Optional[str] = Header(default=None)):
    token = extract_bearer_token(authorization)
    if not token:
        return JSONResponse(status_code=401, content={"error": "Access token required"})

    # Stage 3 will verify this token with Supabase instead of just checking it exists.
    return {"message": "token received, not verified yet"}
