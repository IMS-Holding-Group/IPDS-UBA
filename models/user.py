from werkzeug.security import check_password_hash, generate_password_hash

from database import get_connection


class UserModel:
    @staticmethod
    def get_by_id(user_id):
        conn = get_connection()
        row = conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
        conn.close()
        return row

    @staticmethod
    def get_by_username(username):
        conn = get_connection()
        row = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        return row

    @staticmethod
    def get_by_username_or_email(identifier):
        conn = get_connection()
        row = conn.execute(
            'SELECT * FROM users WHERE username = ? OR email = ?', (identifier, identifier)
        ).fetchone()
        conn.close()
        return row

    @staticmethod
    def create(username, email, password_plain):
        conn = get_connection()
        try:
            conn.execute(
                """
                INSERT INTO users (username, email, password_hash, is_admin, is_active)
                VALUES (?, ?, ?, 0, 1)
            """,
                (username, email, generate_password_hash(password_plain)),
            )
            conn.commit()
            uid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
            conn.close()
            return uid
        except Exception:
            conn.close()
            raise

    @staticmethod
    def verify_password(row, password_plain):
        if not row:
            return False
        return check_password_hash(row['password_hash'], password_plain)

    @staticmethod
    def update_last_login(user_id, when_iso):
        conn = get_connection()
        conn.execute('UPDATE users SET last_login = ? WHERE user_id = ?', (when_iso, user_id))
        conn.commit()
        conn.close()

    @staticmethod
    def change_password(user_id, new_password_plain):
        conn = get_connection()
        conn.execute(
            'UPDATE users SET password_hash = ? WHERE user_id = ?',
            (generate_password_hash(new_password_plain), user_id),
        )
        conn.commit()
        conn.close()
