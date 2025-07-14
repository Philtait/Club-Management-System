# File: app/utils/email.py

from flask_mail import Message
from app.extensions import mail
from flask import url_for, current_app
from threading import Thread
from itsdangerous import URLSafeTimedSerializer


def send_async_email(app, msg):
    """
    Helper to send emails asynchronously.
    """
    with app.app_context():
        mail.send(msg)


def _get_serializer():
    """
    Create a itsdangerous serializer using the app's SECRET_KEY.
    """
    secret_key = current_app.config.get('SECRET_KEY')
    return URLSafeTimedSerializer(secret_key)


def send_reset_email(user):
    """
    Send password-reset instructions to the user.
    """
    s = _get_serializer()
    token = s.dumps(user.email, salt='password-reset')
    reset_link = url_for('auth.reset_token', token=token, _external=True)

    msg = Message("Password Reset Request", recipients=[user.email])
    msg.body = f"""Hi {user.first_name},

You requested to reset your password. Click the link below to proceed:

{reset_link}

If you didn’t request this, simply ignore this email.
"""
    Thread(
        target=send_async_email,
        args=(current_app._get_current_object(), msg)
    ).start()


def send_confirmation_email(user):
    """
    Send welcome + email-confirmation link to a new user.
    """
    s = _get_serializer()
    token = s.dumps(user.email, salt='email-confirm')
    confirm_link = url_for('auth.confirm_email', token=token, _external=True)

    msg = Message("Please Confirm Your Email", recipients=[user.email])
    msg.body = f"""Hi {user.first_name},

Welcome to the CMS! Please confirm your email address by clicking:

{confirm_link}

If you didn’t sign up, just ignore this message.
"""
    Thread(
        target=send_async_email,
        args=(current_app._get_current_object(), msg)
    ).start()


def send_membership_request_email(user, club, recipient_emails):
    """
    Notify club leaders/admins that a student has requested to join a club.
    """
    link = url_for('membership.membership_requests', club_id=club.club_id, _external=True)
    msg = Message(
        subject=f"Membership Request for '{club.name}'",
        recipients=recipient_emails
    )
    msg.body = f"""A new membership request:

Student: {user.first_name} {user.last_name}
Club: {club.name}

Review requests here: {link}
"""
    Thread(
        target=send_async_email,
        args=(current_app._get_current_object(), msg)
    ).start()


def send_membership_approved_email(user, club):
    """
    Notify a student that their club membership has been approved.
    """
    link = url_for('clubs.view_club', club_id=club.club_id, _external=True)
    msg = Message(
        subject=f"Your Membership in '{club.name}' is Approved",
        recipients=[user.email]
    )
    msg.body = f"""Hi {user.first_name},

Great news! Your request to join the club '{club.name}' has been approved.

Visit the club page: {link}
"""
    Thread(
        target=send_async_email,
        args=(current_app._get_current_object(), msg)
    ).start()


def send_membership_rejected_email(user, club):
    """
    Notify a student that their club membership request was rejected.
    """
    msg = Message(
        subject=f"Membership Request for '{club.name}' Rejected",
        recipients=[user.email]
    )
    msg.body = f"""Hi {user.first_name},

We're sorry to inform you that your request to join the club '{club.name}' was not approved.

You may reach out to the club leaders for more information.
"""
    Thread(
        target=send_async_email,
        args=(current_app._get_current_object(), msg)
    ).start()


def send_club_approved_email(user, club):
    """
    Notify a user that their club creation request has been approved.
    """
    link = url_for('clubs.view_club', club_id=club.club_id, _external=True)
    msg = Message(
        subject=f"Your Club '{club.name}' Was Approved",
        recipients=[user.email]
    )
    msg.body = f"""Hi {user.first_name},

Congratulations! The club '{club.name}' you created has been approved.

Visit your new club page: {link}
"""
    Thread(
        target=send_async_email,
        args=(current_app._get_current_object(), msg)
    ).start()


def send_event_created_email(event, recipient_emails):
    """
    Notify club members that a new event has been created.
    """
    link = url_for('events.view_event', event_id=event.event_id, _external=True)
    msg = Message(
        subject=f"New Event: {event.title}",
        recipients=recipient_emails
    )
    msg.body = f"""Hello,

A new event '{event.title}' has been scheduled by the club '{event.club.name}'.
Date: {event.event_date}
Location: {event.location}

View event details: {link}
"""
    Thread(
        target=send_async_email,
        args=(current_app._get_current_object(), msg)
    ).start()


def send_event_registration_email(user, event, recipient_emails):
    """
    Notify club patron or leaders when someone registers for an event.
    """
    link = url_for('events.view_event', event_id=event.event_id, _external=True)
    msg = Message(
        subject=f"New Registration for '{event.title}'",
        recipients=recipient_emails
    )
    msg.body = f"""Hello,

{user.first_name} {user.last_name} has registered for the event '{event.title}'.

View registrations: {link}
"""
    Thread(
        target=send_async_email,
        args=(current_app._get_current_object(), msg)
    ).start()


def send_feedback_received_email(user, feedback):
    """
    Send confirmation to student that their feedback was received.
    """
    event = feedback.event
    msg = Message(
        subject=f"Feedback Received for '{event.title}'",
        recipients=[user.email]
    )
    msg.body = f"""Hi {user.first_name},

Thank you for your feedback on the event '{event.title}'.

We appreciate your input.
"""
    Thread(
        target=send_async_email,
        args=(current_app._get_current_object(), msg)
    ).start()


def send_payment_receipt_email(user, payment):
    """
    Send receipt to student after a payment is completed.
    """
    # Determine link based on payment purpose
    if payment.purpose == 'Membership':
        link = url_for('clubs.view_club', club_id=payment.related_id, _external=True)
    elif payment.purpose == 'Event':
        link = url_for('events.view_event', event_id=payment.related_id, _external=True)
    else:
        link = None

    msg = Message(
        subject=f"Payment Receipt: {payment.purpose}",
        recipients=[user.email]
    )
    msg.body = f"""Hi {user.first_name},

We've received your payment of {payment.amount} for {payment.purpose}.
Transaction code: {payment.transaction_code}
{'Details: ' + link if link else ''}

Thank you!
"""
    Thread(
        target=send_async_email,
        args=(current_app._get_current_object(), msg)
    ).start()


def send_notification_email(user, title, message, related_url=None):
    """
    General-purpose notification email.
    """
    body = f"Hi {user.first_name},\n\n{message}\n"
    if related_url:
        body += f"\nSee more: {related_url}\n"

    msg = Message(subject=title, recipients=[user.email])
    msg.body = body
    Thread(
        target=send_async_email,
        args=(current_app._get_current_object(), msg)
    ).start()
