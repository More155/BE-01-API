import os
from fastapi import FastAPI, HTTPException, Body, Depends, BackgroundTasks
from datetime import datetime
import psycopg
from psycopg.rows import dict_row
from pydantic import BaseModel
from ai_service import AIService
from schemas import ClassificationResult
from fastapi.responses import FileResponse
from report_service import generate_pdf_report_job
from scraper import EthicalScraper

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:mysecretpassword@localhost:5432/myapp")

def get_db_connection():
    try:
        conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@app.post("/data")
def receive_data(payload: dict):
    user_input = payload.get("input", "No input provided")
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO submissions (input_text) VALUES (%s) RETURNING id;",
                (user_input,)
            )
            inserted_id = cur.fetchone()["id"]
            conn.commit()

    return {
        "received": True, 
        "id": inserted_id,
        "yourInput": user_input,
        "storage": "Postgres Database"
    }

@app.get("/data")
def get_all_data():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM submissions;")
            records = cur.fetchall()
    return {"submissions": records}

ai_service = AIService()

class ClassifyRequest(BaseModel):
    text: str

@app.post("/classify", response_model=ClassificationResult)
def classify_message(payload: ClassifyRequest):
    result = ai_service.analyze_text(payload.text)
    return result

@app.post("/reports")
def trigger_report_generation(background_tasks: BackgroundTasks):
    """Triggers report generation as an asynchronous background job."""
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO reports (status) VALUES ('pending') RETURNING id;")
            report_id = cur.fetchone()[0]
            
    background_tasks.add_task(generate_pdf_report_job, report_id)
    
    return {
        "message": "Report generation started in the background",
        "report_id": report_id,
        "status_check_url": f"http://localhost:8080/reports/{report_id}"
    }

@app.get("/reports/{report_id}")
def get_report_status(report_id: int):
    """Allows the client to poll the status of a specific job."""
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT status, artifact_path FROM reports WHERE id = %s", (report_id,))
            result = cur.fetchone()
            
    if not result:
        raise HTTPException(status_code=404, detail="Report job not found")
        
    status, artifact_path = result
    response = {"report_id": report_id, "status": status}
    
    if status == "completed":
        response["download_url"] = f"http://localhost:8080/reports/{report_id}/download"
        
    return response

@app.get("/reports/{report_id}/download")
def download_report_pdf(report_id: int):
    """Streams the completed static PDF file directly to the client's browser/disk."""
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT status, artifact_path FROM reports WHERE id = %s", (report_id,))
            result = cur.fetchone()
            
    if not result or result[0] != "completed":
        raise HTTPException(status_code=400, detail="Report is not completed or does not exist")
        
    artifact_path = result[1]
    
    if not os.path.exists(artifact_path):
        raise HTTPException(status_code=500, detail="Artifact missing on disk storage layer")
        
    return FileResponse(artifact_path, media_type="application/pdf", filename=f"report_{report_id}.pdf")

class ScrapeRequest(BaseModel):
    urls: list[str]

@app.post("/scrape")
def trigger_scraper(payload: ScrapeRequest, background_tasks: BackgroundTasks):
    """
    Exposes the scraper pipeline through an actionable endpoint.
    Uses BackgroundTasks so that long-running network operations don't time out the client.
    """
    def run_scraper_job(urls_to_process: list[str]):
        scraper = EthicalScraper(
            base_url="https://quotes.toscrape.com", 
            bot_name="DataGatheringClassBot",
            contact_email="student@example.com",
            delay=3.0
        )
        for target in urls_to_process:
            record = scraper.run_pipeline(target)
            if record:
                # Appends into your active local working project directory
                with open("rag_corpus.jsonl", "a", encoding="utf-8") as f:
                    f.write(record.model_dump_json() + "\n")
        print("🎉 Scraping job runner execution complete.")

    background_tasks.add_task(run_scraper_job, payload.urls)
    
    return {
        "status": "processing",
        "message": f"Scraper has been spun up in the background for {len(payload.urls)} targets."
    }