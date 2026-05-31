from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from app.config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../app/static')
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    from app.auth.routes import auth_bp
    from app.cases.routes import cases_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(cases_bp)

    @app.route('/')
    def index():
        return redirect(url_for('auth.dashboard'))

    @app.route('/dashboard')
    def dashboard_home():
        return redirect(url_for('auth.dashboard'))

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    return app

from flask import render_template