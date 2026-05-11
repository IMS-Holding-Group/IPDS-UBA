import numpy as np


def analyze_url(url):
    if not url:
        return 0.0
    score = 0.0
    suspicious_keywords = [
        'login',
        'signin',
        'account',
        'verify',
        'secure',
        'update',
        'bank',
        'paypal',
        'password',
    ]
    url_lower = url.lower()
    for kw in suspicious_keywords:
        if kw in url_lower:
            score += 0.15
    if url.count('.') > 3:
        score += 0.2
    rest = url
    if '://' in url:
        rest = url.split('://', 1)[1]
    if '..' in rest or '%' in rest:
        score += 0.25
    if '@' in rest:
        score += 0.25
    if len(url) > 100:
        score += 0.1
    return min(score, 1.0)


def extract_features_array(activity_data):
    url_score = analyze_url(activity_data.get('url_address', ''))
    features = [
        float(activity_data.get('typing_speed', 5.0)),
        float(activity_data.get('login_hour', 12)),
        float(activity_data.get('failed_attempts', 0)),
        float(activity_data.get('session_duration', 300)),
        url_score,
    ]
    return np.array(features, dtype=float).reshape(1, -1), url_score
