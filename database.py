import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any
DB_PATH = 'voiceguard.db'

def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('\n        CREATE TABLE IF NOT EXISTS analysis_history (\n            id INTEGER PRIMARY KEY AUTOINCREMENT,\n            filename TEXT NOT NULL,\n            timestamp TEXT NOT NULL,\n            deepfake_label TEXT NOT NULL,\n            deepfake_confidence REAL NOT NULL,\n            watermark_confidence REAL NOT NULL,\n            risk_score REAL NOT NULL,\n            final_verdict TEXT NOT NULL,\n            risk_level TEXT NOT NULL\n        )\n    ')
    conn.commit()
    conn.close()

def save_analysis(filename: str, deepfake_label: str, deepfake_confidence: float, watermark_confidence: float, risk_score: float, final_verdict: str, risk_level: str) -> None:
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('\n        INSERT INTO analysis_history (\n            filename, timestamp, deepfake_label, deepfake_confidence, \n            watermark_confidence, risk_score, final_verdict, risk_level\n        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)\n    ', (filename, timestamp, deepfake_label, deepfake_confidence, watermark_confidence, risk_score, final_verdict, risk_level))
    conn.commit()
    conn.close()

def fetch_all_history() -> List[Dict[str, Any]]:
    if not os.path.exists(DB_PATH):
        init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM analysis_history ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def clear_history() -> None:
    if not os.path.exists(DB_PATH):
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM analysis_history')
        cursor.execute('DELETE FROM sqlite_sequence WHERE name="analysis_history"')
        conn.commit()
    except sqlite3.Error as e:
        print(f'Database error during clear_history: {e}')
    finally:
        if conn:
            conn.close()
