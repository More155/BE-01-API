import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, Body, Depends, BackgroundTasks
from datetime import datetime
import psycopg
from psycopg.rows import dict_row
from pydantic import BaseModel
from ai_service import AIService
from schemas import ClassificationResult
from fastapi.responses import FileResponse, JSONResponse
from report_service import generate_pdf_report_job
from scraper import EthicalScraper
from tasks_db import get_tasks_db_connection, init_tasks_db
from auth import router as auth_router, AuthError, auth_error_handler

app = FastAPI(
    title="BE-01 API",
    description="FlyRank backend track project. Supabase Auth secures /auth/logout, /protected/profile and /protected/dashboard — click Authorize and paste an access_token from /auth/login.",
)
app.include_router(auth_router)
app.add_exception_handler(AuthError, auth_error_handler)

init_tasks_db()


def task_row_to_dict(row):
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}


@app.get("/tasks")
def list_tasks():
    with get_tasks_db_connection() as conn:
        rows = conn.execute("SELECT * FROM tasks").fetchall()
    return [task_row_to_dict(row) for row in rows]


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    with get_tasks_db_connection() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        return JSONResponse(status_code=404, content={"error": "Task not found"})
    return task_row_to_dict(row)


@app.post("/tasks", status_code=201)
def create_task(payload: dict = Body(...)):
    title = payload.get("title")
    if not title or not isinstance(title, str):
        return JSONResponse(status_code=400, content={"error": "title is required"})
    done = bool(payload.get("done", False))

    with get_tasks_db_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO tasks (title, done) VALUES (?, ?)", (title, done)
        )
        conn.commit()
        task_id = cursor.lastrowid

    return {"id": task_id, "title": title, "done": done}


@app.put("/tasks/{task_id}")
def update_task(task_id: int, payload: dict = Body(...)):
    with get_tasks_db_connection() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is None:
            return JSONResponse(status_code=404, content={"error": "Task not found"})

        title = payload.get("title", row["title"])
        if not title or not isinstance(title, str):
            return JSONResponse(status_code=400, content={"error": "title is required"})
        done = bool(payload.get("done", row["done"]))

        conn.execute(
            "UPDATE tasks SET title = ?, done = ? WHERE id = ?", (title, done, task_id)
        )
        conn.commit()

    return {"id": task_id, "title": title, "done": done}


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    with get_tasks_db_connection() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is None:
            return JSONResponse(status_code=404, content={"error": "Task not found"})
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()

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