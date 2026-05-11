from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from models.alert import AlertModel

alerts_bp = Blueprint('alerts', __name__)


def _require_login():
    if not session.get('user_id'):
        return redirect(url_for('auth.login_view'))
    return None


@alerts_bp.route('/alerts')
def alerts_view():
    red = _require_login()
    if red:
        return red
    return render_template('alerts.html', page_title='التنبيهات الأمنية')


@alerts_bp.route('/api/alerts')
def api_alerts_list():
    try:
        if not session.get('user_id'):
            return jsonify({'ok': False, 'message': 'غير مصرّح'}), 401
        uid = int(session['user_id'])
        severity = request.args.get('severity') or None
        status = request.args.get('status') or None
        rows = AlertModel.list_for_user(uid, severity=severity, status=status)
        items = []
        for r in rows:
            desc = r['description'] or ''
            main_desc = desc
            reasons_text = ''
            if '|||' in desc:
                parts = desc.split('|||', 1)
                main_desc = parts[0]
                reasons_text = parts[1] if len(parts) > 1 else ''
            items.append(
                {
                    'alert_id': r['alert_id'],
                    'threat_type': r['threat_type'],
                    'severity_level': r['severity_level'],
                    'alert_timestamp': r['alert_timestamp'],
                    'alert_status': r['alert_status'],
                    'description': main_desc,
                    'reasons_text': reasons_text,
                    'activity_id': r['activity_id'],
                }
            )
        return jsonify({'ok': True, 'items': items})
    except Exception as e:
        return jsonify({'ok': False, 'message': str(e)}), 500


@alerts_bp.route('/api/alert/update', methods=['POST'])
def api_alert_update():
    try:
        if not session.get('user_id'):
            return jsonify({'ok': False, 'message': 'غير مصرّح'}), 401
        uid = int(session['user_id'])
        data = request.get_json(silent=True) or {}
        alert_id = int(data.get('alert_id', 0))
        new_status = (data.get('status') or '').strip()
        allowed = {'جديد', 'قيد المراجعة', 'مغلق'}
        if new_status not in allowed:
            return jsonify({'ok': False, 'message': 'حالة غير صالحة'}), 400
        n = AlertModel.update_status(alert_id, uid, new_status)
        if not n:
            return jsonify({'ok': False, 'message': 'لم يتم العثور على التنبيه'}), 404
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'message': str(e)}), 500


@alerts_bp.route('/api/alerts/delete', methods=['POST'])
def api_delete_alert():
    try:
        if not session.get('user_id'):
            return jsonify({'ok': False, 'message': 'غير مصرّح'}), 401
        uid = int(session['user_id'])
        data = request.get_json(silent=True) or {}
        alert_id = int(data.get('alert_id', 0))
        if alert_id <= 0:
            return jsonify({'ok': False, 'message': 'معرّف غير صالح'}), 400
        n = AlertModel.delete_by_id(alert_id, uid)
        if not n:
            return jsonify({'ok': False, 'message': 'لم يُعثر على التنبيه'}), 404
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'message': str(e)}), 500


@alerts_bp.route('/api/alerts/summary')
def api_alerts_summary():
    try:
        if not session.get('user_id'):
            return jsonify({'ok': False, 'message': 'غير مصرّح'}), 401
        uid = int(session['user_id'])
        high = AlertModel.count_high_open_for_user(uid)
        active = AlertModel.count_active_for_user(uid)
        return jsonify({'ok': True, 'high_new': high, 'active': active})
    except Exception as e:
        return jsonify({'ok': False, 'message': str(e)}), 500
