from datetime import datetime

from database import get_connection


class BehaviorProfileModel:
    @staticmethod
    def get_for_user(user_id):
        conn = get_connection()
        row = conn.execute(
            'SELECT * FROM behavior_profiles WHERE user_id = ?', (user_id,)
        ).fetchone()
        conn.close()
        return row

    @staticmethod
    def ensure_row(user_id):
        conn = get_connection()
        row = conn.execute(
            'SELECT * FROM behavior_profiles WHERE user_id = ?', (user_id,)
        ).fetchone()
        if not row:
            conn.execute(
                """
                INSERT INTO behavior_profiles (user_id, avg_typing_speed, typical_login_hours, avg_session_duration, common_url_patterns)
                VALUES (?, ?, ?, ?, ?)
            """,
                (user_id, 5.0, str(int(datetime.utcnow().hour)), 0.0, ''),
            )
            conn.commit()
            row = conn.execute(
                'SELECT * FROM behavior_profiles WHERE user_id = ?', (user_id,)
            ).fetchone()
        conn.close()
        return row

    @staticmethod
    def update_after_activity(user_id, typing_speed, login_hour, session_duration, url_path):
        row = BehaviorProfileModel.ensure_row(user_id)
        old_avg = float(row['avg_typing_speed'] or 5.0)
        new_avg = round(old_avg * 0.7 + float(typing_speed) * 0.3, 2)
        hours = row['typical_login_hours'] or ''
        parts = [p for p in hours.split(',') if p.strip()]
        lh = str(int(login_hour))
        if lh not in parts:
            parts.append(lh)
        parts = parts[-12:]
        hours_str = ','.join(parts)
        old_sess = float(row['avg_session_duration'] or 0.0)
        sd = float(session_duration or 0.0)
        new_sess = round(old_sess * 0.85 + sd * 0.15, 1) if sd > 0 else old_sess
        urls = row['common_url_patterns'] or ''
        up = urls
        if url_path:
            segs = [s for s in urls.split(',') if s][:8]
            if url_path not in segs:
                segs.append(url_path[:120])
            up = ','.join(segs[-8:])
        conn = get_connection()
        conn.execute(
            """
            UPDATE behavior_profiles
            SET avg_typing_speed = ?, typical_login_hours = ?, avg_session_duration = ?, common_url_patterns = ?, profile_updated = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """,
            (new_avg, hours_str, new_sess, up, user_id),
        )
        conn.commit()
        conn.close()
