import os
from dotenv import load_dotenv
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    # Secret key for CSRF protection and sessions
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration: fallback to SQLite if DATABASE_URL is not provided.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Mail settings
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')  # This should be your App Password
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME')
    MAIL_MAX_EMAILS = 5
    MAIL_ASCII_ATTACHMENTS = False
    MAIL_SUPPRESS_SEND = False
    MAIL_DEBUG = True  # Enable for debugging

    # Admin settings
    ADMINS = [os.environ.get('ADMIN_EMAIL')]

    WTF_CSRF_ENABLED = True  # Ensure CSRF protection is enabled
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY') or 'your-csrf-secret-key'

    # Pagination setting for any paged views
    POSTS_PER_PAGE = 10
