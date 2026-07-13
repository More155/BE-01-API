import os
from fastapi import FastAPI, HTTPException, Body, Depends
from datetime import datetime
import psycopg
from psycopg.rows import dict_row
from pydantic import BaseModel
from ai_service import AIService
from schemas import ClassificationResult

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