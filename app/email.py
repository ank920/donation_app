from flask import current_app, render_template, url_for
from flask_mail import Message
from app import mail
from threading import Thread
import logging

logger = logging.getLogger(__name__)

def send_async_email(app, msg):
    with app.app_context():
        try:
            logger.info(f"Attempting to send email to {msg.recipients}")
            mail.send(msg)
            logger.info(f"Successfully sent email to {msg.recipients}")
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            raise

def send_email(subject, sender, recipients, text_body, html_body):
    try:
        msg = Message(subject, sender=sender, recipients=recipients)
        msg.body = text_body
        msg.html = html_body
        
        logger.info(f"Creating email thread for {recipients}")
        Thread(target=send_async_email,
               args=(current_app._get_current_object(), msg)).start()
        return True
    except Exception as e:
        logger.error(f"Error preparing email: {str(e)}")
        return False

def send_password_reset_email(user):
    try:
        token = user.get_reset_password_token()
        logger.info(f"Generated reset token for user {user.email}")
        
        reset_url = url_for('auth.reset_password', token=token, _external=True)
        logger.info(f"Reset URL generated: {reset_url}")
        
        return send_email(
            '[Donation App] Reset Your Password',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[user.email],
            text_body=f'''To reset your password, visit the following link:
{reset_url}

If you did not request a password reset, simply ignore this message.
''',
            html_body=f'''
<p>Dear {user.username},</p>
<p>To reset your password, <a href="{reset_url}">click here</a>.</p>
<p>Alternatively, you can paste the following link in your browser's address bar:</p>
<p>{reset_url}</p>
<p>If you did not request a password reset, simply ignore this message.</p>
<p>Best regards,<br>The Donation App Team</p>
''')
    except Exception as e:
        logger.error(f"Error sending password reset email: {str(e)}")
        return False 