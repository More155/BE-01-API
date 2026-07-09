from fastapi import FastAPI
from datetime import datetime

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@app.post("/data")
def receive_data(payload: dict):
    return {"received": True, "yourInput": payload.get("input", "No input provided")}