# Stage 7 — the rematch prompt (after comparing v1 to my hand-built version)

> Build a FastAPI backend that uses Supabase for authentication. Same five routes as
> before (`POST /auth/signup`, `POST /auth/login`, `POST /auth/logout`,
> `GET /protected/profile`, `GET /public/info`), but this time:
>
> - Every error response body must be exactly `{"error": "<message>"}` — not FastAPI's
>   default `{"detail": ...}` shape. This applies to validation errors too, so don't
>   rely on Pydantic's automatic 422 for a missing `email`/`password`: check for their
>   presence yourself and return 400 with that error shape before calling Supabase.
> - `/auth/logout` must revoke the specific session tied to the bearer token the caller
>   presented in *this* request — not whatever session happens to be cached on a shared
>   client instance. Assume this server is stateless and may be handling multiple users'
>   requests concurrently on one process.
> - Never use the `service_role` key anywhere, including for logout.
> - Add a second protected route (e.g. `/protected/dashboard`) that reuses the exact
>   same guard as `/protected/profile`, to prove the auth check isn't duplicated per route.

**What changed in one sentence:** the rematch prompt pins down the exact error JSON
shape, explicitly calls out that Supabase validation must happen before Pydantic's
automatic 422, and spells out that logout has to target the caller's own token on a
stateless/concurrent server — the three things v1 got wrong because I never said them.
