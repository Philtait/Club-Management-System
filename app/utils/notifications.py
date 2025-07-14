# File: app/utils/notifications.py

from flask import current_app
from flask_mail import Message
from app.extensions import mail, db
from app.models import Notification, UserNotification, User

def send_notification(title, message, notification_type, related_id, user_ids):
    """
    Create a Notification and UserNotification for each user_id in user_ids.
    """
    # 1) Create the notification record
    notif = Notification(
        title=title,
        message=message,
        notification_type=notification_type,
        related_id=related_id
    )
    db.session.add(notif)
    db.session.flush()  # assign notif.notification_id

    # 2) Create per-user links
    for uid in user_ids:
        un = UserNotification(user_id=uid, notification_id=notif.notification_id)
        db.session.add(un)

    db.session.commit()
    return notif

def send_email(to, subject, template, **kwargs):
    """
    Sends an email using Flask-Mail. `template` is a Jinja2 template under templates/email/.
    """
    msg = Message(
        subject=f"[CMS] {subject}",
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[to]
    )
    # Render both text and HTML versions if you have them
    msg.body = current_app.jinja_env.get_template(f"email/{template}.txt").render(**kwargs)
    msg.html = current_app.jinja_env.get_template(f"email/{template}.html").render(**kwargs)
    mail.send(msg)
