from database import get_connection


class AlertModel:
    @staticmethod
    def create(user_id, threat_type, severity_level, description, activity_id=None, status='جديد'):
        conn = get_connection()
        cur = conn.execute(
            """
            INSERT INTO alerts (user_id, threat_type, severity_level, alert_status, activity_id, description)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (user_id, threat_type, severity_level, status, activity_id, description),
        )
        conn.commit()
        aid = cur.lastrowid
        conn.close()
        return aid

    @staticmethod
    def count_active_for_user(user_id):
        conn = get_connection()
        n = conn.execute(
            """
            SELECT COUNT(*) AS c FROM alerts
            WHERE user_id = ? AND alert_status != 'مغلق'
        """,
            (user_id,),
        ).fetchone()['c']
        conn.close()
        return n

    @staticmethod
    def count_for_user(user_id):
        conn = get_connection()
        n = conn.execute('SELECT COUNT(*) AS c FROM alerts WHERE user_id = ?', (user_id,)).fetchone()['c']
        conn.close()
        return n

    @staticmethod
    def count_high_open_for_user(user_id):
        conn = get_connection()
        n = conn.execute(
            """
            SELECT COUNT(*) AS c FROM alerts
            WHERE user_id = ? AND severity_level = 'عالية' AND alert_status = 'جديد'
        """,
            (user_id,),
        ).fetchone()['c']
        conn.close()
        return n

    @staticmethod
    def list_for_user(user_id, severity=None, status=None):
        conn = get_connection()
        where = ['user_id = ?']
        params = [user_id]
        if severity:
            where.append('severity_level = ?')
            params.append(severity)
        if status:
            where.append('alert_status = ?')
            params.append(status)
        wsql = ' AND '.join(where)
        rows = conn.execute(
            f"""
            SELECT * FROM alerts WHERE {wsql}
            ORDER BY alert_timestamp DESC
        """,
            params,
        ).fetchall()
        conn.close()
        return rows

    @staticmethod
    def update_status(alert_id, user_id, new_status):
        conn = get_connection()
        cur = conn.execute(
            """
            UPDATE alerts SET alert_status = ?
            WHERE alert_id = ? AND user_id = ?
        """,
            (new_status, alert_id, user_id),
        )
        conn.commit()
        changed = cur.rowcount
        conn.close()
        return changed

    @staticmethod
    def delete_by_id(alert_id, user_id):
        conn = get_connection()
        cur = conn.execute(
            'DELETE FROM alerts WHERE alert_id = ? AND user_id = ?',
            (alert_id, user_id),
        )
        conn.commit()
        n = cur.rowcount
        conn.close()
        return n
