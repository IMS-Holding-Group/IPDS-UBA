from routes.auth import auth_bp, set_behavior_analyzer
from routes.dashboard import dashboard_bp
from routes.activities import activities_bp
from routes.alerts import alerts_bp

__all__ = [
    'auth_bp',
    'dashboard_bp',
    'activities_bp',
    'alerts_bp',
    'set_behavior_analyzer',
]
