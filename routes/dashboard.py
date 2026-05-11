from datetime import datetime, timedelta

from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from models.activity import ActivityModel
from models.alert import AlertModel
from models.behavior_profile import BehaviorProfileModel
from models.user import UserModel

dashboard_bp = Blueprint('dashboard', __name__)


def _require_login():
    if not session.get('user_id'):
        return redirect(url_for('auth.login_view'))
    return None


@dashboard_bp.route('/dashboard')
def dashboard_view():
    red = _require_login()
    if red:
        return red
    return render_template('dashboard.html', page_title='لوحة التحكم')


@dashboard_bp.route('/profile', methods=['GET', 'POST'])
def profile_view():
    red = _require_login()
    if red:
        return red
    uid = int(session['user_id'])
    msg = None
    err = None
    if request.method == 'POST':
        old_p = request.form.get('old_password') or ''
        new_p = request.form.get('new_password') or ''
        new_p2 = request.form.get('new_password2') or ''
        row = UserModel.get_by_id(uid)
        if not UserModel.verify_password(row, old_p):
            err = 'كلمة المرور الحالية غير صحيحة'
        elif len(new_p) < 6:
            err = 'كلمة المرور الجديدة قصيرة جداً'
        elif new_p != new_p2:
            err = 'تأكيد كلمة المرور غير متطابق'
        else:
            UserModel.change_password(uid, new_p)
            msg = 'تم تحديث كلمة المرور بنجاح'
    user = UserModel.get_by_id(uid)
    profile = BehaviorProfileModel.get_for_user(uid)
    total_act = ActivityModel.count_for_user(uid)
    total_alerts = AlertModel.count_for_user(uid)
    normal = ActivityModel.count_normal_for_user(uid)
    sec = round((normal / total_act) * 100, 1) if total_act else 100.0
    return render_template(
        'profile.html',
        page_title='الملف الشخصي',
        user=user,
        profile=profile,
        total_act=total_act,
        total_alerts=total_alerts,
        security_rate=sec,
        msg=msg,
        err=err,
    )


@dashboard_bp.route('/api/stats')
def api_stats():
    try:
        if not session.get('user_id'):
            return jsonify({'ok': False, 'message': 'غير مصرّح'}), 401
        uid = int(session['user_id'])
        total = ActivityModel.count_for_user(uid)
        normal = ActivityModel.count_normal_for_user(uid)
        active_alerts = AlertModel.count_active_for_user(uid)
        rate = round((normal / total) * 100, 1) if total else 100.0
        row = UserModel.get_by_id(uid)
        last_login = row['last_login'] if row else None
        raw_chart = ActivityModel.chart_last_days(uid, 7)
        days_map = {r['d']: {'normal': int(r['normal_cnt'] or 0), 'suspicious': int(r['susp_cnt'] or 0)} for r in raw_chart}
        chart = []
        for i in range(6, -1, -1):
            d = (datetime.utcnow().date() - timedelta(days=i)).isoformat()
            entry = days_map.get(d, {'normal': 0, 'suspicious': 0})
            chart.append({'date': d, 'normal': entry['normal'], 'suspicious': entry['suspicious']})
        sidebar_alerts = AlertModel.count_active_for_user(uid)
        return jsonify(
            {
                'ok': True,
                'total_activities': total,
                'active_alerts': active_alerts,
                'security_rate': rate,
                'last_login': last_login,
                'chart': chart,
                'sidebar_alerts': sidebar_alerts,
            }
        )
    except Exception as e:
        return jsonify({'ok': False, 'message': str(e)}), 500


@dashboard_bp.route('/api/activities/recent')
def api_activities_recent():
    try:
        if not session.get('user_id'):
            return jsonify({'ok': False, 'message': 'غير مصرّح'}), 401
        uid = int(session['user_id'])
        limit = int(request.args.get('limit', 20))
        limit = max(1, min(limit, 100))
        rows = ActivityModel.recent_for_user(uid, limit)
        out = []
        for r in rows:
            out.append(
                {
                    'activity_id': r['activity_id'],
                    'timestamp': r['timestamp'],
                    'activity_type': r['activity_type'],
                    'url_address': r['url_address'],
                    'is_suspicious': int(r['is_suspicious'] or 0),
                }
            )
        return jsonify({'ok': True, 'items': out})
    except Exception as e:
        return jsonify({'ok': False, 'message': str(e)}), 500
