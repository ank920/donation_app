from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from config import Config
from datetime import datetime

# Global extensions
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()  # Initialize CSRF protection once
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)  # Initialize CSRF after app is defined
    migrate.init_app(app, db)

    # Add custom template filter for datetime formatting
    @app.template_filter('format_datetime')
    def format_datetime(value):
        if value:
            # Format the date only
            return value.strftime('%d/%m/%Y')
        return ''

    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # Register blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    from app.donations import bp as donations_bp
    app.register_blueprint(donations_bp, url_prefix='/donations')

    # For development: create tables if they don't exist
    with app.app_context():
        db.create_all()

    return app

from app import models
