## Assignment Solution: Docker & Postgres Integration

### 1. Architectural Integrity
As required by the assignment guidelines, the core service layer and API routes have remained completely untouched from Assignment 2. By leveraging structural layering, the underlying volatile in-memory storage repository was seamlessly swapped for a real PostgreSQL implementation by updating only the entry point connection logic.

### 2. Proof of Data Persistence
Persistence was manually tested and proven using Postman via the following flow:
1. Triggered a `POST` request to `http://localhost:8080/data` sending a JSON payload. The row was successfully written to the Postgres container.
2. Ran `docker compose down` to stop and remove all active app and database container layers.
3. Restarted the entire local stack in one command via `docker compose up`.
4. Triggered a `GET` request to `http://localhost:8080/data` in Postman. The previously stored record was successfully retrieved from the database, proving that the data persists across system restarts due to the configured Docker named volume.

---

## Week 4 Feature: AI API Integration (Structured Output & Telemetry)

### 1. Abstract Provider Seam
The integration isolates LLM interactions into an independent interface module (`ai_service.py`). The rest of the FastAPI application routes do not interact directly with the underlying SDK. By swapping the `AI_PROVIDER` flag inside the `.env` file, the underlying API engine can be globally targeted without changing any routing code, establishing an isolated architectural seam.

### 2. Schema-Validated JSON & Fault Tolerance
The `POST /classify` endpoint requests structured tracking data from the `gemini-flash-latest` model. The raw response is strictly parsed and validated against a Pydantic structure definition (`schemas.py`), ensuring that malformed formatting is gracefully handled rather than crashing the operational thread. Network safety protections include a timeout cap on outbound transactions along with localized retry routines designed to back off during brief 429/5xx anomalies while instantly blocking 400 client-side failures.

### 3. Telemetry & Cost Line Monitoring
Every transaction actively computes standard production pricing calculations mapped against input and output tokens. The terminal logs track the operations dynamically using the following structure:
`[AI LOG - Feature: Text Classification] Input Tokens: <count> | Output Tokens: <count> | Estimated Cost: $<calculated_amount>`