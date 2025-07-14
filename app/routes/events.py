# File: app/routes/events.py

from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.extensions import db
from app.forms import EventForm
from app.models import Event, Club, EventRegistration, Admin, User
from app.utils.notifications import send_notification
from app.utils.email import (
    send_event_registration_email,
    send_event_created_email
)

events_bp = Blueprint("events", __name__, url_prefix="/events")


@events_bp.route("/")
@login_required
def list_events():
    now = datetime.utcnow()
    events = (
        Event.query
             .filter(Event.event_date >= now)
             .order_by(Event.event_date.asc())
             .all()
    )
    return render_template("events/events.html", events=events, now=now)


@events_bp.route("/<int:event_id>")
@login_required
def view_event(event_id):
    event = Event.query.get_or_404(event_id)
    now = datetime.utcnow()

    already_registered = False
    if current_user.role == "Student" and current_user.student:
        already_registered = (
            EventRegistration.query
                .filter_by(event_id=event_id,
                           student_id=current_user.student.student_id)
                .first() is not None
        )

    registration_closed = (
        event.registration_deadline and event.registration_deadline < now
    )

    can_submit_feedback = False
    if (
        current_user.role == "Student" and
        event.event_date < now and
        current_user.student
    ):
        can_submit_feedback = True

    return render_template(
        "events/view_event.html",
        event=event,
        already_registered=already_registered,
        registration_closed=registration_closed,
        can_submit_feedback=can_submit_feedback
    )


@events_bp.route("/register/<int:event_id>", methods=["POST"])
@login_required
def register(event_id):
    if current_user.role != "Student":
        flash("Only students can register for events.", "warning")
        return redirect(url_for("events.view_event", event_id=event_id))

    event = Event.query.get_or_404(event_id)
    now = datetime.utcnow()
    if event.registration_deadline and event.registration_deadline < now:
        flash("Registration for this event is closed.", "danger")
        return redirect(url_for("events.view_event", event_id=event_id))

    existing = (
        EventRegistration.query
            .filter_by(event_id=event_id,
                       student_id=current_user.student.student_id)
            .first()
    )
    if existing:
        flash("You are already registered.", "info")
    else:
        reg = EventRegistration(
            event_id=event_id,
            student_id=current_user.student.student_id,
            registered_on=datetime.utcnow()
        )
        db.session.add(reg)
        db.session.commit()

        # Notify the club patron admin via DB + email
        patron = Admin.query.get(event.club.patron_admin_id)
        if patron:
            recipient = User.query.get(patron.user_id)
            title = "New Event Registration"
            msg   = f"{current_user.first_name} {current_user.last_name} " \
                    f"registered for '{event.title}'."

            # DB notification
            send_notification(title, msg, "Event", event.event_id, [recipient.user_id])

            # Email notification
            send_event_registration_email(
                current_user,
                event,
                [recipient.email]
            )

        flash("You have been registered for the event!", "success")

    return redirect(url_for("events.view_event", event_id=event_id))


@events_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_event():
    if current_user.role not in ("Admin", "ClubLeader"):
        flash("You do not have permission to create events.", "danger")
        return redirect(url_for("events.list_events"))

    form = EventForm()
    clubs = Club.query.all() if current_user.role == "Admin" else [
        cl.club for cl in current_user.club_leaderships
    ]
    form.club_id.choices = [(c.club_id, c.name) for c in clubs]

    if form.validate_on_submit():
        event = Event(
            club_id=form.club_id.data,
            title=form.title.data,
            description=form.description.data,
            location=form.location.data,
            event_date=form.event_date.data,
            registration_deadline=form.registration_deadline.data,
            max_attendees=form.max_attendees.data,
            created_at=datetime.utcnow()
        )
        db.session.add(event)
        db.session.commit()

        # Notify all active club members via DB + email
        club = Club.query.get(event.club_id)
        members = [m for m in club.memberships if m.left_on is None]
        user_ids = [m.student.user_id for m in members]
        emails   = [m.student.user.email for m in members]
        title    = "New Event Created"
        msg      = f"A new event '{event.title}' has been scheduled for {club.name}."

        send_notification(title, msg, "Event", event.event_id, user_ids)
        send_event_created_email(event, emails)

        flash("Event created successfully!", "success")
        return redirect(url_for("events.list_events"))

    return render_template("events/create_event.html", form=form)
