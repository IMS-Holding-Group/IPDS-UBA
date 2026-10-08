import os
import sqlite3
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), 'ipds.db')


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            account_creation_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME,
            is_admin INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS activities (
            activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            activity_type TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            url_address TEXT,
            ip_address TEXT,
            typing_speed REAL,
            login_hour INTEGER,
            failed_attempts INTEGER DEFAULT 0,
            session_duration REAL,
            is_suspicious INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts (
            alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            threat_type TEXT NOT NULL,
            severity_level TEXT NOT NULL,
            alert_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            alert_status TEXT DEFAULT 'جديد',
            activity_id INTEGER,
            description TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (activity_id) REFERENCES activities(activity_id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS behavior_profiles (
            profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            avg_typing_speed REAL,
            typical_login_hours TEXT,
            avg_session_duration REAL,
            common_url_patterns TEXT,
            profile_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """
    )

    conn.commit()
    conn.close()


def seed_default_users():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) AS c FROM users')
    row = cur.fetchone()
    if row and row['c'] > 0:
        conn.close()
        return
    cur.execute(
        """
        INSERT INTO users (username, email, password_hash, is_admin, is_active)
        VALUES (?, ?, ?, 1, 1)
    """,
        ('admin', 'admin@ipds.local', generate_password_hash('')),
    )
    cur.execute(
        """
        INSERT INTO users (username, email, password_hash, is_admin, is_active)
        VALUES (?, ?, ?, 0, 1)
    """,
        ('testuser', 'testuser@ipds.local', generate_password_hash('')),
    )
    conn.commit()
    uid_admin = cur.execute("SELECT user_id FROM users WHERE username='admin'").fetchone()[0]
    uid_test = cur.execute("SELECT user_id FROM users WHERE username='testuser'").fetchone()[0]
    cur.execute(
        """
        INSERT INTO behavior_profiles (user_id, avg_typing_speed, typical_login_hours, avg_session_duration, common_url_patterns)
        VALUES (?, ?, ?, ?, ?)
    """,
        (uid_admin, 5.5, '9,10,11,14,15', 420.0, '/login,/dashboard'),
    )
    cur.execute(
        """
        INSERT INTO behavior_profiles (user_id, avg_typing_speed, typical_login_hours, avg_session_duration, common_url_patterns)
        VALUES (?, ?, ?, ?, ?)
    """,
        (uid_test, 4.8, '8,9,12,16', 360.0, '/login,/activities'),
    )
    cur.execute(
        """
        INSERT INTO activities (user_id, activity_type, url_address, ip_address, typing_speed, login_hour, failed_attempts, session_duration, is_suspicious)
        VALUES (?, 'تسجيل دخول', ?, '127.0.0.1', 5.2, 10, 0, 180, 0)
    """,
        (uid_test, 'http://127.0.0.1:5000/login'),
    )
    aid = cur.lastrowid
    cur.execute(
        """
        INSERT INTO alerts (user_id, threat_type, severity_level, alert_status, activity_id, description)
        VALUES (?, 'نشاط مشبوه', 'متوسطة', 'جديد', ?, 'تنبيه تجريبي لاختبار الواجهة')
    """,
        (uid_test, aid),
    )
    conn.commit()
    conn.close()
