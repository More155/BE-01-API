# Stage 7 — the prompt (written from memory, before rereading the assignment)

> Build a FastAPI backend that uses Supabase for authentication. I need:
> - `POST /auth/signup` — takes email and password, creates a Supabase user
> - `POST /auth/login` — takes email and password, logs the user in and returns the access token
> - `POST /auth/logout` — logs the user out, needs to be authenticated
> - `GET /protected/profile` — returns the current user's info, only for logged in users
> - `GET /public/info` — just returns a public message, no auth needed
>
> Use environment variables for the Supabase URL and key. Add a dependency/middleware
> that checks the Authorization header for a Bearer token and verifies it with Supabase
> before letting the request through to protected routes. Make sure FastAPI's Swagger
> docs show a lock icon and let me authorize with a bearer token. Return proper status
> codes: 201 for signup, 200 for login, 204 for logout, 400 for bad input, 401 for
> missing or bad tokens.

This is deliberately what I could reconstruct from memory, not a copy of the assignment
doc. Looking back at it next to the doc, it's missing: the exact `{"error": ...}` JSON
shape, "never use the service_role key," what counts as a "malformed" header, and any
mention of a second protected route to prove the guard is reusable.
