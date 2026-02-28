"""
database.py

Initializes and manages a lightweight SQLite database for the Aawaaz 
authentication framework to maintain a persistent processing history.
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any

DB_PATH = "voiceguard.db"

def init_db() -> None:
    """
    Initializes the SQLite database. Creates the 'analysis_history' 
    table if it does not already exist.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            deepfake_label TEXT NOT NULL,
            deepfake_confidence REAL NOT NULL,
            watermark_confidence REAL NOT NULL,
            risk_score REAL NOT NULL,
            final_verdict TEXT NOT NULL,
            risk_level TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def save_analysis(
    filename: str,
    deepfake_label: str,
    deepfake_confidence: float,
    watermark_confidence: float,
    risk_score: float,
    final_verdict: str,
    risk_level: str
) -> None:
    """
    Saves an analysis record into the database.
    
    Args:
        filename (str): The name of the analyzed file.
        deepfake_label (str): The predicted deepfake class ('real' or 'fake').
        deepfake_confidence (float): Confidence score of the deepfake prediction.
        watermark_confidence (float): Confidence score of the watermark detection.
        risk_score (float): The final computed risk percentage.
        final_verdict (str): The human-readable string summarizing the assessment.
        risk_level (str): The categorical risk level ('Low', 'Medium', 'High').
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO analysis_history (
            filename, timestamp, deepfake_label, deepfake_confidence, 
            watermark_confidence, risk_score, final_verdict, risk_level
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        filename, timestamp, deepfake_label, deepfake_confidence, 
        watermark_confidence, risk_score, final_verdict, risk_level
    ))
    conn.commit()
    conn.close()

def fetch_all_history() -> List[Dict[str, Any]]:
    """
    Retrieves all processing history from the database, sorted newest first.
    
    Returns:
        List[Dict[str, Any]]: A list of dictionaries representing past analysis records.
    """
    # Ensure DB is initialized before fetching
    if not os.path.exists(DB_PATH):
        init_db()
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enables column access by name
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM analysis_history ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def clear_history() -> None:
    """
    Deletes all temporary analysis records from the 'analysis_history' table.
    The table structure is kept intact.
    """
    if not os.path.exists(DB_PATH):
        return
        
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Delete all rows without dropping the table
        cursor.execute('DELETE FROM analysis_history')
        # Reset the auto-increment counter
        cursor.execute('DELETE FROM sqlite_sequence WHERE name="analysis_history"')
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error during clear_history: {e}")
    finally:
        if conn:
            conn.close()
