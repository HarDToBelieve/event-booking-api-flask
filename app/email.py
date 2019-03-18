from flask_mail import Message

from config import Config
from app import app, mail
from app.common import queue_deferred


def send_email_aysnc(message):
    with app.app_context():
        mail.send(message)


def send_email(subject, recipients, text_body, html_body, _async=True):
    message = Message(subject=subject, sender=Config.EMAIL_SENDER,
                      recipients=recipients, body=text_body, html=html_body)
    if _async:
        queue_deferred(send_email_aysnc, message)
    else:
        mail.send(message)
