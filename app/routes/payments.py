# File: app/routes/payments.py

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from app.extensions import db
from app.models import MpesaPayment, Membership, Club, Student
from app.forms import MpesaPaymentForm
from app.utils.email import send_payment_receipt_email
import uuid

payments_bp = Blueprint("payments", __name__, url_prefix="/payments")


def admin_required(f):
    """Decorator to ensure the current_user is an Admin."""
    @wraps(f)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "Admin":
            flash("Access denied – Admins only.", "warning")
            return redirect(url_for("dashboard.dashboard"))
        return f(*args, **kwargs)
    return decorated_view


@payments_bp.route("/", methods=["GET", "POST"])
@login_required
def pay_membership():
    if current_user.role != "Student":
        flash("Only students can make payments.", "warning")
        return redirect(url_for("dashboard.dashboard"))

    form = MpesaPaymentForm()
    memberships = Membership.query.filter_by(
        student_id=current_user.student.student_id,
        left_on=None
    ).all()
    form.club_id.choices = [(m.club_id, m.club.name) for m in memberships]

    if form.validate_on_submit():
        tx_code = f"MPESA{uuid.uuid4().hex[:10].upper()}"
        payment = MpesaPayment(
            student_id=current_user.student.student_id,
            transaction_code=tx_code,
            amount=form.amount.data,
            purpose='Membership',
            related_id=form.club_id.data,
            status='Pending'
        )
        db.session.add(payment)
        db.session.commit()
        flash("Payment initiated. Check your M-PESA for the prompt.", "info")
        return redirect(url_for("payments.list_payments"))

    return render_template("payments/pay_membership.html", form=form)


@payments_bp.route("/history")
@login_required
def list_payments():
    if current_user.role != "Student":
        return redirect(url_for("dashboard.dashboard"))

    payments = (MpesaPayment.query
                .filter_by(student_id=current_user.student.student_id)
                .order_by(MpesaPayment.created_at.desc())
                .all())
    return render_template("payments/payment_history.html", payments=payments)


@payments_bp.route("/callback", methods=["POST"])
def mpesa_callback():
    data = request.get_json() or {}
    tx_code = data.get("transaction_code")
    status  = data.get("status")
    payment = MpesaPayment.query.filter_by(transaction_code=tx_code).first()
    if payment and status in ("Completed", "Failed"):
        payment.status = status
        db.session.commit()
    return ("", 204)


@payments_bp.route("/admin/pending")
@login_required
@admin_required
def admin_pending_payments():
    payments = MpesaPayment.query.filter_by(status="Pending").all()
    return render_template("payments/payment_history.html", payments=payments)


@payments_bp.route("/admin/mark-paid/<int:payment_id>", methods=["POST"])
@login_required
@admin_required
def mark_paid(payment_id):
    payment = MpesaPayment.query.get_or_404(payment_id)
    payment.status = "Completed"
    db.session.commit()

    # Send receipt email
    student = Student.query.get(payment.student_id)
    send_payment_receipt_email(student.user, payment)

    flash(f"Payment {payment.transaction_code} marked as completed and student notified.", "success")
    return redirect(url_for("payments.admin_pending_payments"))
