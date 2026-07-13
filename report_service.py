import os
from datetime import datetime
import psycopg
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

DATABASE_URL = os.getenv("DATABASE_URL")
STORAGE_DIR = "./storage"

os.makedirs(STORAGE_DIR, exist_ok=True)

def generate_pdf_report_job(report_id: int):
    artifact_path = f"{STORAGE_DIR}/report_{report_id}.pdf"
    
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*), DATE(created_at) 
                    FROM submissions 
                    GROUP BY DATE(created_at)
                    ORDER BY DATE(created_at) DESC;
                """)
                aggregated_data = cur.fetchall()

        c = canvas.Canvas(artifact_path, pagesize=letter)
        c.drawString(100, 750, f"System Executive Report - Job #{report_id}")
        c.drawString(100, 730, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        c.line(100, 720, 500, 720)

        y_position = 690
        c.drawString(100, y_position, "Date | Total Submissions")
        y_position -= 20
        
        for count, date in aggregated_data:
            c.drawString(100, y_position, f"{date} : {count} records")
            y_position -= 20
            if y_position < 50:
                c.showPage()
                y_position = 750
                
        c.save() 
        
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE reports 
                    SET status = 'completed', artifact_path = %s, completed_at = %s 
                    WHERE id = %s
                """, (artifact_path, datetime.now(), report_id))
                
    except Exception as e:
        print(f"Background Job Failed: {str(e)}")
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE reports SET status = 'failed' WHERE id = %s", (report_id,))