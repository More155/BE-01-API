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


## Week 4: Asynchronous PDF Report Generator (Background Jobs)

### 1. Architectural Overview
To optimize API performance and prevent HTTP timeouts, the PDF reporting engine is decoupled into an asynchronous producer-consumer pattern using FastAPI's `BackgroundTasks`. 

* **Trigger (`POST /reports`)**: Inserts a tracking record with a `pending` status into PostgreSQL and immediately yields a response payload containing the unique `report_id` to the client.
* **Worker Execution**: Runs in a background thread executing data warehouse aggregations via `psycopg` on the active database storage engine.
* **Artifact Layout Engine**: Synthesizes and draws dynamic graphical components onto a local disk storage layer using `reportlab`.
* **Verification & Delivery (`GET /reports/{id}/download`)**: Streams the compiled structural PDF back to the system client using an optimized chunked `FileResponse`.

---

### 2. Verified Workflow Logs & Postman Execution

The end-to-end background lifecycle was verified locally via Postman across three phases:

#### Phase A: Job Dispatching
* **Endpoint**: `POST http://localhost:8080/reports`
* **Response Payload**:
    ```json
    {
        "message": "Report generation started in the background",
        "report_id": 2,
        "status_check_url": "http://localhost:8080/reports/2"
    }
    ```

#### Phase B: Asynchronous State Transitions (Polling)
* **Endpoint**: `GET http://localhost:8080/reports/2`
* **Response Payload (Processing / Complete)**:
    ```json
    {
        "report_id": 2,
        "status": "completed",
        "download_url": "http://localhost:8080/reports/2/download"
    }
    ```

#### Phase C: Local Storage & Binary Artifact Streaming
* **Endpoint**: `GET http://localhost:8080/reports/2/download`
* **Result**: Postman successfully captures the streamable header and opens a structural PDF canvas displaying automated database telemetry counts grouped by date/status. Wiping or restarting containers does not risk structural data state corruption as the output layer interacts cleanly via Docker storage rules.

---

## Week 5 Feature: Ethical Web Scraper & Background Data Pipeline

### 1. Pipeline Architecture
To prepare a high-quality corpus for downstream RAG integration, this service implements an ethical web scraping and parsing pipeline:
* **Fetch (`requests` / `httpx`)**: Retrieves targeted web pages asynchronously using descriptive user identification headers.
* **Parse (`BeautifulSoup4`)**: Parses HTML responses and extracts structured target attributes (e.g., page text, quotes, author metadata, tags).
* **Clean & Structure**: Sanitizes extracted text and maps raw records into schema-validated models.
* **Persist (`psycopg`)**: Inserts normalized records into PostgreSQL database tables with conflict handling to avoid duplicating target records.

### 2. Professionalism Layer & Ethical Bot Behavior
* **`robots.txt` Compliance**: Queries and parses target site directives prior to crawling to respect disallowed paths and crawl delays.
* **Rate-Limiting & Politeness**: Enforces interval delays between consecutive network calls to prevent overwhelming remote host bandwidth.
* **Identifiable User-Agent**: Transmits customized HTTP `User-Agent` identification headers identifying the bot and providing contact details for webmasters.

### 3. Execution Flow (`POST /scrape`)

#### Request Payload
* **Endpoint**: `POST http://localhost:8080/scrape`
* **Body**:
    ```json
    {
      "urls": [
        "[https://quotes.toscrape.com/page/1/](https://quotes.toscrape.com/page/1/)",
        "[https://quotes.toscrape.com/page/2/](https://quotes.toscrape.com/page/2/)"
      ]
    }
    ```

#### Response Payload
```json
{
  "status": "processing",
  "message": "Scraper has been spun up in the background for 2 targets."
}