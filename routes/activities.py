from math import ceil

from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from models.activity import ActivityModel

activities_bp = Blueprint('activities', __name__)


def _require_login():
    if not session.get('user_id'):
        return redirect(url_for('auth.login_view'))
    return None


@activities_bp.route('/activities')
def activities_view():
    red = _require_login()
    if red:
        return red
    uid = int(session['user_id'])
    page = int(request.args.get('page', 1) or 1)
    if page < 1:
        page = 1
    per_page = 20
    activity_type = request.args.get('type') or None
    suspicious_param = request.args.get('suspicious', '')
    susp_filter = suspicious_param if suspicious_param in ('0', '1') else None
    date_from = request.args.get('date_from') or None
    date_to = request.args.get('date_to') or None
    total, rows = ActivityModel.list_paginated(
        uid, page, per_page, activity_type, susp_filter, date_from, date_to
    )
    types = ActivityModel.distinct_types_for_user(uid)
    total_pages = max(1, int(ceil(total / per_page)))
    return render_template(
        'activities.html',
        page_title='سجل النشاطات',
        rows=rows,
        page=page,
        total_pages=total_pages,
        total=total,
        types=types,
        activity_type=activity_type or '',
        suspicious=suspicious_param,
        date_from=date_from or '',
        date_to=date_to or '',
    )


@activities_bp.route('/api/activities/delete', methods=['POST'])
def api_delete_activity():
    try:
        if not session.get('user_id'):
            return jsonify({'ok': False, 'message': 'غير مصرّح'}), 401
        uid = int(session['user_id'])
        data = request.get_json(silent=True) or {}
        aid = int(data.get('activity_id', 0))
        if aid <= 0:
            return jsonify({'ok': False, 'message': 'معرّف غير صالح'}), 400
        n = ActivityModel.delete_by_id(aid, uid)
        if not n:
            return jsonify({'ok': False, 'message': 'لم يُعثر على السجل'}), 404
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'message': str(e)}), 500
