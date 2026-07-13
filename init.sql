CREATE TABLE IF NOT EXISTS submissions (
    id SERIAL PRIMARY KEY,
    input_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    status VARCHAR(20) DEFAULT 'pending', -- pending, completed, failed
    artifact_path VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);