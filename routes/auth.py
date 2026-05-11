from datetime import datetime
from urllib.parse import urlparse

from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from models.activity import ActivityModel
from models.alert import AlertModel
from models.behavior_profile import BehaviorProfileModel
from models.user import UserModel

auth_bp = Blueprint('auth', __name__)

_analyzer = None


def set_behavior_analyzer(analyzer):
    global _analyzer
    _analyzer = analyzer


def _failure_key(identifier):
    return 'login_failures_' + (identifier or 'unknown')


def _client_ip():
    return request.remote_addr or '0.0.0.0'


@auth_bp.route('/', methods=['GET', 'POST'])
@auth_bp.route('/login', methods=['GET', 'POST'])
def login_view():
    if request.method == 'GET':
        if session.get('user_id'):
            return redirect(url_for('dashboard.dashboard_view'))
        return render_template('login.html')
    try:
        wants_json = request.is_json or request.headers.get('Content-Type', '').startswith('application/json')
        if wants_json:
            data = request.get_json(silent=True) or {}
            identifier = (data.get('username') or '').strip()
            password = data.get('password') or ''
            typing_speed = float(data.get('typing_speed', 5.0))
            login_hour = int(data.get('login_hour', 12))
            url_address = data.get('url_address') or ''
            session_duration = float(data.get('session_duration', 0.0))
        else:
            identifier = (request.form.get('username') or '').strip()
            password = request.form.get('password') or ''
            typing_speed = 5.0
            login_hour = datetime.now().hour
            url_address = request.url_root + 'login'
            session_duration = 0.0

        fk = _failure_key(identifier)
        fails_before = int(session.get(fk, 0))
        row = UserModel.get_by_username_or_email(identifier)
        activity_base = {
            'typing_speed': typing_speed,
            'login_hour': login_hour,
            'failed_attempts': fails_before,
            'session_duration': session_duration,
            'url_address': url_address,
        }

        if not row or not UserModel.verify_password(row, password):
            session[fk] = fails_before + 1
            if row:
                uid_for_log = int(row['user_id'])
                ad = dict(activity_base)
                ad['failed_attempts'] = int(session.get(fk, 0))
                res = _analyzer.analyze(ad, uid_for_log)
                ActivityModel.insert(
                    uid_for_log,
                    'محاولة دخول فاشلة',
                    url_address=url_address,
                    ip_address=_client_ip(),
                    typing_speed=typing_speed,
                    login_hour=login_hour,
                    failed_attempts=ad['failed_attempts'],
                    session_duration=session_duration,
                    is_suspicious=1 if res['is_suspicious'] else 0,
                )
            if wants_json:
                return jsonify({'success': False, 'message': 'بيانات الدخول غير صحيحة'}), 200
            return render_template('login.html', error='بيانات الدخول غير صحيحة')

        if not row['is_active']:
            if wants_json:
                return jsonify({'success': False, 'message': 'الحساب غير مفعّل'}), 200
            return render_template('login.html', error='الحساب غير مفعّل')

        session.pop(fk, None)
        uid = int(row['user_id'])
        ad = dict(activity_base)
        ad['failed_attempts'] = 0
        analysis = _analyzer.analyze(ad, uid)
        now_iso = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        UserModel.update_last_login(uid, now_iso)
        aid = ActivityModel.insert(
            uid,
            'تسجيل دخول',
            url_address=url_address,
            ip_address=_client_ip(),
            typing_speed=typing_speed,
            login_hour=login_hour,
            failed_attempts=0,
            session_duration=session_duration,
            is_suspicious=1 if analysis['is_suspicious'] else 0,
        )
        if analysis['is_suspicious']:
            desc = analysis.get('description') or ''
            reasons = analysis.get('reasons') or []
            if reasons:
                desc = desc + '|||' + '؛ '.join(reasons)
            AlertModel.create(
                uid,
                analysis['threat_type'] or 'نشاط مشبوه',
                analysis['severity_level'] or 'منخفضة',
                desc,
                activity_id=aid,
            )
        try:
            path_only = urlparse(url_address).path or url_address
        except Exception:
            path_only = url_address
        BehaviorProfileModel.update_after_activity(uid, typing_speed, login_hour, session_duration, path_only)

        session['user_id'] = uid
        session['username'] = row['username']
        session['is_admin'] = int(row['is_admin'] or 0)

        alert_message = ''
        if analysis['is_suspicious']:
            parts = '؛ '.join(analysis.get('reasons') or [])
            alert_message = (analysis.get('description') or '') + (' — ' + parts if parts else '')

        if wants_json:
            return jsonify(
                {
                    'success': True,
                    'suspicious': bool(analysis['is_suspicious']),
                    'alert_message': alert_message,
                }
            )
        return redirect(url_for('dashboard.dashboard_view'))
    except Exception as e:
        if request.is_json or request.headers.get('Content-Type', '').startswith('application/json'):
            return jsonify({'success': False, 'message': 'حدث خطأ في الخادم', 'detail': str(e)}), 500
        return render_template('login.html', error='حدث خطأ في الخادم')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register_view():
    if request.method == 'GET':
        if session.get('user_id'):
            return redirect(url_for('dashboard.dashboard_view'))
        return render_template('register.html')
    try:
        username = (request.form.get('username') or '').strip()
        email = (request.form.get('email') or '').strip()
        password = request.form.get('password') or ''
        password2 = request.form.get('password2') or ''
        if not username or not email or not password:
            return render_template('register.html', error='يرجى تعبئة جميع الحقول')
        if password != password2:
            return render_template('register.html', error='كلمتا المرور غير متطابقتين')
        UserModel.create(username, email, password)
        return redirect(url_for('auth.login_view'))
    except Exception:
        return render_template('register.html', error='تعذر إنشاء الحساب (ربما الاسم أو البريد مستخدم)')


@auth_bp.route('/logout')
def logout_view():
    session.clear()
    return redirect(url_for('auth.login_view'))


@auth_bp.route('/api/analyze', methods=['POST'])
def api_analyze():
    try:
        if not session.get('user_id'):
            return jsonify({'ok': False, 'message': 'يجب تسجيل الدخول'}), 401
        data = request.get_json(silent=True) or {}
        uid = int(session['user_id'])
        activity_data = {
            'typing_speed': float(data.get('typing_speed', 5.0)),
            'login_hour': int(data.get('login_hour', 12)),
            'failed_attempts': int(data.get('failed_attempts', 0)),
            'session_duration': float(data.get('session_duration', 300)),
            'url_address': data.get('url_address') or '',
        }
        result = _analyzer.analyze(activity_data, uid)
        return jsonify({'ok': True, 'result': result})
    except Exception as e:
        return jsonify({'ok': False, 'message': str(e)}), 500
