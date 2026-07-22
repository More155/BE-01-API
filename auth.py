from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from supabase import AuthApiError

from auth_service import supabase

router = APIRouter()

bearer_scheme = HTTPBearer(auto_error=False)


class AuthError(HTTPException):
    """Raised by the auth guard so its JSON body is {"error": ...} instead of FastAPI's default {"detail": ...}."""


async def auth_error_handler(request: Request, exc: AuthError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


def get_bearer_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
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


@router.post("/auth/logout", status_code=204)
def logout(user=Depends(get_current_user), token: str = Depends(get_bearer_token)):
    # supabase.auth.sign_out() only signs out this client's own local session, which
    # is never set in a stateless per-request server. admin.sign_out(token) revokes the
    # specific session the caller presented instead — it still only needs the anon key
    # (the token itself carries the authority), never the service_role key.
    supabase.auth.admin.sign_out(token, "local")


@router.get("/public/info")
def public_info():
    return {"message": "Welcome stranger! This info is public."}


@router.get("/protected/profile")
def get_profile(user=Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "created_at": user.created_at,
    }


@router.get("/protected/dashboard")
def get_dashboard(user=Depends(get_current_user)):
    return {"message": f"Welcome to your dashboard, {user.email}"}
