## Assignment Solution: Docker & Postgres Integration

### 1. Architectural Integrity
As required by the assignment guidelines, the core service layer and API routes have remained completely untouched from Assignment 2. By leveraging structural layering, the underlying volatile in-memory storage repository was seamlessly swapped for a real PostgreSQL implementation by updating only the entry point connection logic.

### 2. Proof of Data Persistence
Persistence was manually tested and proven using Postman via the following flow:
1. Triggered a `POST` request to `http://localhost:8080/data` sending a JSON payload. The row was successfully written to the Postgres container.
2. Ran `docker compose down` to stop and remove all active app and database container layers.
3. Restarted the entire local stack in one command via `docker compose up`.
4. Triggered a `GET` request to `http://localhost:8080/data` in Postman. The previously stored record was successfully retrieved from the database, proving that the data persists across system restarts due to the configured Docker named volume.