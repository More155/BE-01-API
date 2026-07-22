from typing import Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from supabase import AuthApiError

from auth_service import supabase

router = APIRouter()


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
