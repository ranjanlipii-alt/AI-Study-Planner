import sqlite3
import os
from datetime import datetime

DB_DIR = "database"
DB_PATH = os.path.join(DB_DIR, "study_planner.db")

def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Subjects and topics table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            topic TEXT NOT NULL,
            exam_date TEXT NOT NULL,
            difficulty INTEGER NOT NULL, -- 1 (Easy) to 5 (Hard)
            confidence INTEGER NOT NULL, -- 1 (Low) to 5 (High)
            estimated_hours REAL NOT NULL,
            completed INTEGER DEFAULT 0
        )
    """)
    
    # Study log table for tracking revision
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS study_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER,
            date_logged TEXT,
            hours_studied REAL,
            FOREIGN KEY (topic_id) REFERENCES topics(id)
        )
    """)
    conn.commit()
    conn.close()

def add_topic(subject, topic, exam_date, difficulty, confidence, estimated_hours):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO topics (subject, topic, exam_date, difficulty, confidence, estimated_hours, completed)
        VALUES (?, ?, ?, ?, ?, ?, 0)
    """, (subject, topic, exam_date, difficulty, confidence, estimated_hours))
    conn.commit()
    conn.close()

def get_all_topics():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, subject, topic, exam_date, difficulty, confidence, estimated_hours, completed FROM topics")
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_topic_status(topic_id, completed_flag):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE topics SET completed = ? WHERE id = ?", (completed_flag, topic_id))
    conn.commit()
    conn.close()

def log_study_time(topic_id, hours):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("INSERT INTO study_logs (topic_id, date_logged, hours_studied) VALUES (?, ?, ?)", 
                   (topic_id, today, hours))
    conn.commit()
    conn.close()

def get_logged_study_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.subject, SUM(l.hours_studied)
        FROM study_logs l
        JOIN topics t ON l.topic_id = t.id
        GROUP BY t.subject
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows
