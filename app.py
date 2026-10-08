import os

from flask import Flask

from database import init_db, seed_default_users
from ml.behavior_analyzer import BehaviorAnalyzer
from routes.activities import activities_bp
from routes.alerts import alerts_bp
from routes.auth import auth_bp, set_behavior_analyzer
from routes.dashboard import dashboard_bp

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', '')

analyzer = BehaviorAnalyzer()
set_behavior_analyzer(analyzer)


def startup():
    init_db()
    seed_default_users()
    if not analyzer.is_trained:
        analyzer.train_with_simulated_data()


startup()

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(activities_bp)
app.register_blueprint(alerts_bp)


@app.after_request
def security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '').lower() in ('1', 'true', 'yes')
    app.run(host='127.0.0.1', port=port, debug=debug)
