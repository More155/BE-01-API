import os
import sqlite3

TASKS_DB_PATH = os.path.join(os.path.dirname(__file__), "tasks.db")

SEED_TASKS = [
    ("Buy milk", 0),
    ("Write weekly report", 0),
    ("Walk the dog", 1),
]


def get_tasks_db_connection():
    conn = sqlite3.connect(TASKS_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_tasks_db():
    with get_tasks_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done BOOLEAN NOT NULL DEFAULT 0
            )
            """
        )
        count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        if count == 0:
            conn.executemany(
                "INSERT INTO tasks (title, done) VALUES (?, ?)", SEED_TASKS
            )
        conn.commit()
