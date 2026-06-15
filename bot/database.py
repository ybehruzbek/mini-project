import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "qalb_taskini.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Dastlabki bosqichda sxema yangilanishi uchun eski jadvallarni o'chiramiz
    cursor.execute("DROP TABLE IF EXISTS Daily_Progress")
    cursor.execute("DROP TABLE IF EXISTS Dhikrs")
    cursor.execute("DROP TABLE IF EXISTS Users")

    # Users jadvallari (yoshni endi oralig'li TEXT sifatida olamiz)
    cursor.execute("""
        CREATE TABLE Users (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            age TEXT,
            gender TEXT,
            habit_level TEXT,
            timezone TEXT DEFAULT 'Asia/Tashkent',
            streak_days INTEGER DEFAULT 0,
            last_active DATE
        )
    """)

    # Dhikrs jadvallari
    cursor.execute("""
        CREATE TABLE Dhikrs (
            dhikr_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            target_count INTEGER DEFAULT 100,
            FOREIGN KEY(user_id) REFERENCES Users(user_id)
        )
    """)

    # Daily_Progress jadvallari
    cursor.execute("""
        CREATE TABLE Daily_Progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            dhikr_id INTEGER,
            date DATE,
            current_count INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES Users(user_id),
            FOREIGN KEY(dhikr_id) REFERENCES Dhikrs(dhikr_id),
            UNIQUE(user_id, dhikr_id, date)
        )
    """)

    conn.commit()
    conn.close()

def save_user_data(user_id, data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Users (user_id, full_name, age, gender, habit_level)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            full_name=excluded.full_name,
            age=excluded.age,
            gender=excluded.gender,
            habit_level=excluded.habit_level
    """, (user_id, data.get('full_name'), data.get('age'), data.get('gender'), data.get('habit_level')))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM Users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def add_default_dhikr(user_id, habit_level):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Odatiga qarab kunlik maqsadni belgilaymiz. Yangi boshlovchilar uchun biroz kamroq, qolganlar uchun 100 ta.
    target = 33 if habit_level == 'beginner' else 100
    
    dhikrs = [
        ("Astagʻfirullahil aʼziym va atubi ilayh", target),
        ("Hasbunallohu va ni'mal vakil", target),
        ("Ya Malikul Mulk", target)
    ]
    
    for title, tgt in dhikrs:
        cursor.execute("""
            INSERT INTO Dhikrs (user_id, title, target_count)
            SELECT ?, ?, ?
            WHERE NOT EXISTS (SELECT 1 FROM Dhikrs WHERE user_id=? AND title=?)
        """, (user_id, title, tgt, user_id, title))
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Ma'lumotlar bazasi muvaffaqiyatli yaratildi/yangilandi.")
