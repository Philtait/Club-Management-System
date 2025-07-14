# File: app/routes/membership.py

from flask import (
    Blueprint, render_template, redirect,
    url_for, flash, abort, request
)
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models.membership import Membership
from app.models.club_leader import ClubLeader
from app.models.club import Club
from app.models.notification import Notification, UserNotification
from app.models.student import Student
from app.utils.email import (
    send_membership_request_email,
    send_membership_approved_email,
    send_membership_rejected_email,
)

membership_bp = Blueprint("membership", __name__, url_prefix="/membership")


@membership_bp.route("/join/<int:club_id>", methods=["POST"])
@login_required
def join_club(club_id):
    # Only students can request membership
    if current_user.role != "Student":
        flash("Only students can request to join clubs.", "warning")
        return redirect(url_for("clubs.view_club", club_id=club_id))

    student_id = current_user.student.student_id

    # Check for any existing membership record
    existing = Membership.query.filter_by(
        student_id=student_id,
        club_id=club_id
    ).first()

    if existing:
        if existing.status == "Pending":
            flash("Your membership request is already pending approval.", "info")
        elif existing.status == "Approved":
            flash("You are already a member of this club.", "info")
        else:  # Rejected
            existing.status    = "Pending"
            existing.joined_on = datetime.utcnow()
            existing.left_on   = None
            db.session.commit()
            flash("Your request has been resubmitted and is pending approval.", "success")
        return redirect(url_for("clubs.view_club", club_id=club_id))

    # Create a new membership request
    membership = Membership(
        student_id=student_id,
        club_id=club_id,
        status="Pending",
        joined_on=datetime.utcnow()
    )
    db.session.add(membership)
    db.session.commit()
    flash("Membership request sent. Awaiting approval.", "success")

    # Notify all club leaders via DB notifications and email
    club = Club.query.get_or_404(club_id)
    leaders = ClubLeader.query.filter_by(club_id=club_id).all()
    if leaders:
        # DB notifications
        notif = Notification(
            title="New Membership Request",
            message=(
                f"{current_user.student.user.first_name} "
                f"{current_user.student.user.last_name} "
                f"has requested to join {club.name}"
            ),
            notification_type="Club",
            related_id=membership.membership_id,
            via_email=True
        )
        db.session.add(notif)
        db.session.flush()  # populate notif.notification_id

        for lead in leaders:
            un = UserNotification(
                user_id=lead.user_id,
                notification_id=notif.notification_id
            )
            db.session.add(un)
        db.session.commit()

        # Email notifications
        recipient_emails = [lead.user.email for lead in leaders]
        send_membership_request_email(
            current_user.student.user,
            club,
            recipient_emails
        )

    return redirect(url_for("clubs.view_club", club_id=club_id))


@membership_bp.route("/leave/<int:club_id>", methods=["POST"])
@login_required
def leave_club(club_id):
    # Only students can leave
    if current_user.role != "Student":
        flash("Only students can leave clubs.", "warning")
        return redirect(url_for("clubs.view_club", club_id=club_id))

    student_id = current_user.student.student_id
    membership = Membership.query.filter_by(
        student_id=student_id,
        club_id=club_id,
        status="Approved",
        left_on=None
    ).first()

    if membership:
        membership.left_on = datetime.utcnow()
        db.session.commit()
        flash("You have left the club.", "success")
    else:
        flash("You are not currently an active member.", "info")

    return redirect(url_for("clubs.view_club", club_id=club_id))


@membership_bp.route("/requests/<int:club_id>")
@login_required
def membership_requests(club_id):
    # Only ClubLeaders of this club can view
    is_leader = ClubLeader.query.filter_by(
        club_id=club_id,
        user_id=current_user.user_id
    ).first()
    if not is_leader:
        abort(403)

    # Fetch only Pending requests, eager-loading student → user
    pending = (
        Membership.query
        .filter_by(club_id=club_id, status="Pending")
        .options(
            joinedload(Membership.student)
              .joinedload(Student.user)
        )
        .order_by(Membership.joined_on.desc())
        .all()
    )

    club = Club.query.get_or_404(club_id)
    return render_template(
        "clubs/membership_requests.html",
        club=club,
        memberships=pending
    )


@membership_bp.route("/requests/<int:club_id>/approve/<int:mid>", methods=["POST"])
@login_required
def approve_member(club_id, mid):
    # Guard: only leaders
    is_leader = ClubLeader.query.filter_by(
        club_id=club_id,
        user_id=current_user.user_id
    ).first()
    if not is_leader:
        abort(403)

    m = Membership.query.get_or_404(mid)
    if m.club_id != club_id:
        abort(404)

    m.status    = "Approved"
    m.joined_on = datetime.utcnow()
    db.session.commit()

    # DB notification for the student
    club = Club.query.get_or_404(club_id)
    notif = Notification(
        title="Membership Approved",
        message=(
            f"Hi {m.student.user.first_name}, your membership in '{club.name}' has been approved."
        ),
        notification_type="Club",
        related_id=m.membership_id,
        via_email=False
    )
    db.session.add(notif)
    db.session.flush()
    user_notif = UserNotification(
        user_id=m.student.user.user_id,
        notification_id=notif.notification_id
    )
    db.session.add(user_notif)
    db.session.commit()

    # Email notification
    send_membership_approved_email(m.student.user, club)
    flash("Member approved and notified.", "success")

    return redirect(request.referrer or f"/membership/requests/{club_id}")


@membership_bp.route("/requests/<int:club_id>/reject/<int:mid>", methods=["POST"])
@login_required
def reject_member(club_id, mid):
    # Guard: only leaders
    is_leader = ClubLeader.query.filter_by(
        club_id=club_id,
        user_id=current_user.user_id
    ).first()
    if not is_leader:
        abort(403)

    m = Membership.query.get_or_404(mid)
    if m.club_id != club_id:
        abort(404)

    m.status = "Rejected"
    db.session.commit()

    # DB notification for the student
    club = Club.query.get_or_404(club_id)
    notif = Notification(
        title="Membership Rejected",
        message=(
            f"Hi {m.student.user.first_name}, your membership request for '{club.name}' was rejected."
        ),
        notification_type="Club",
        related_id=m.membership_id,
        via_email=False
    )
    db.session.add(notif)
    db.session.flush()
    user_notif = UserNotification(
        user_id=m.student.user.user_id,
        notification_id=notif.notification_id
    )
    db.session.add(user_notif)
    db.session.commit()

    # Email notification
    send_membership_rejected_email(m.student.user, club)
    flash("Membership request rejected and student notified.", "info")

    return redirect(request.referrer or f"/membership/requests/{club_id}")
