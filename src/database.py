import sqlite3
import json
import os
from datetime import datetime

class Database:
    def __init__(self, db_path="data\\chats.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()
    
    def init_db(self):
        """Ініціалізація бази даних"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                chat_name TEXT,
                analysis_date TIMESTAMP,
                analysis_result TEXT,
                unfulfilled_count INTEGER
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_analysis(self, chat_id, chat_name, analysis):
        """Збереження результатів аналізу"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO chat_analysis 
            (chat_id, chat_name, analysis_date, analysis_result, unfulfilled_count)
            VALUES (?, ?, ?, ?, ?)
        """, (
            chat_id,
            chat_name,
            datetime.now(),
            json.dumps(analysis, ensure_ascii=False),
            analysis.get('unfulfilled_count', 0)
        ))
        
        conn.commit()
        conn.close()