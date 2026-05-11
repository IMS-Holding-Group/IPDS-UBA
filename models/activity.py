from datetime import datetime, timedelta

from database import get_connection


class ActivityModel:
    @staticmethod
    def insert(
        user_id,
        activity_type,
        url_address=None,
        ip_address=None,
        typing_speed=None,
        login_hour=None,
        failed_attempts=0,
        session_duration=None,
        is_suspicious=0,
    ):
        conn = get_connection()
        cur = conn.execute(
            """
            INSERT INTO activities (
                user_id, activity_type, url_address, ip_address,
                typing_speed, login_hour, failed_attempts, session_duration, is_suspicious
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                user_id,
                activity_type,
                url_address,
                ip_address,
                typing_speed,
                login_hour,
                failed_attempts,
                session_duration,
                int(is_suspicious),
            ),
        )
        conn.commit()
        aid = cur.lastrowid
        conn.close()
        return aid

    @staticmethod
    def count_for_user(user_id):
        conn = get_connection()
        n = conn.execute(
            'SELECT COUNT(*) AS c FROM activities WHERE user_id = ?', (user_id,)
        ).fetchone()['c']
        conn.close()
        return n

    @staticmethod
    def count_normal_for_user(user_id):
        conn = get_connection()
        n = conn.execute(
            'SELECT COUNT(*) AS c FROM activities WHERE user_id = ? AND is_suspicious = 0',
            (user_id,),
        ).fetchone()['c']
        conn.close()
        return n

    @staticmethod
    def recent_for_user(user_id, limit=20):
        conn = get_connection()
        rows = conn.execute(
            """
            SELECT * FROM activities WHERE user_id = ?
            ORDER BY timestamp DESC LIMIT ?
        """,
            (user_id, limit),
        ).fetchall()
        conn.close()
        return rows

    @staticmethod
    def recent_for_user_limit(user_id, limit=10):
        return ActivityModel.recent_for_user(user_id, limit)

    @staticmethod
    def chart_last_days(user_id, days=7):
        conn = get_connection()
        since = (datetime.utcnow() - timedelta(days=days - 1)).strftime('%Y-%m-%d')
        rows = conn.execute(
            """
            SELECT date(timestamp) AS d,
                   SUM(CASE WHEN is_suspicious = 0 THEN 1 ELSE 0 END) AS normal_cnt,
                   SUM(CASE WHEN is_suspicious = 1 THEN 1 ELSE 0 END) AS susp_cnt
            FROM activities
            WHERE user_id = ? AND date(timestamp) >= date(?)
            GROUP BY date(timestamp)
            ORDER BY d
        """,
            (user_id, since),
        ).fetchall()
        conn.close()
        return rows

    @staticmethod
    def list_paginated(user_id, page, per_page, activity_type=None, suspicious=None, date_from=None, date_to=None):
        conn = get_connection()
        where = ['user_id = ?']
        params = [user_id]
        if activity_type:
            where.append('activity_type = ?')
            params.append(activity_type)
        if suspicious is not None and suspicious != '':
            where.append('is_suspicious = ?')
            params.append(int(suspicious))
        if date_from:
            where.append("date(timestamp) >= date(?)")
            params.append(date_from)
        if date_to:
            where.append("date(timestamp) <= date(?)")
            params.append(date_to)
        wsql = ' AND '.join(where)
        total = conn.execute(f'SELECT COUNT(*) AS c FROM activities WHERE {wsql}', params).fetchone()['c']
        offset = (page - 1) * per_page
        params2 = list(params) + [per_page, offset]
        rows = conn.execute(
            f"""
            SELECT * FROM activities WHERE {wsql}
            ORDER BY timestamp DESC LIMIT ? OFFSET ?
        """,
            params2,
        ).fetchall()
        conn.close()
        return total, rows

    @staticmethod
    def distinct_types_for_user(user_id):
        conn = get_connection()
        rows = conn.execute(
            'SELECT DISTINCT activity_type FROM activities WHERE user_id = ? ORDER BY activity_type',
            (user_id,),
        ).fetchall()
        conn.close()
        return [r['activity_type'] for r in rows]

    @staticmethod
    def delete_by_id(activity_id, user_id):
        conn = get_connection()
        conn.execute(
            'UPDATE alerts SET activity_id = NULL WHERE activity_id = ? AND user_id = ?',
            (activity_id, user_id),
        )
        cur = conn.execute(
            'DELETE FROM activities WHERE activity_id = ? AND user_id = ?',
            (activity_id, user_id),
        )
        conn.commit()
        n = cur.rowcount
        conn.close()
        return n
