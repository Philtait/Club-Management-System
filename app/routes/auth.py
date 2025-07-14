# File: app/routes/auth.py

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models.user import User
from app.models.student import Student
from app.models.admin import Admin
from app.forms import (
    LoginForm,
    RegistrationForm,
    RequestResetForm,
    ResetPasswordForm
)
from app.utils.email import send_reset_email, send_confirmation_email
from app import s  # itsdangerous serializer


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            flash("Logged in successfully.", "success")
            next_page = request.args.get("next") or url_for("dashboard.dashboard")
            return redirect(next_page)
        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))

    form = RegistrationForm()
    if form.validate_on_submit():
        # Check for duplicate email before creating
        if User.query.filter_by(email=form.email.data).first():
            flash(
                "That email is already registered. Please log in or use a different email.",
                "warning",
            )
            return render_template("auth/register.html", form=form)

        # Create user
        user = User(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone=form.phone.data,
            gender=form.gender.data,
            role=form.role.data,
            password_hash=generate_password_hash(form.password.data)
        )
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("An unexpected error occurred. Please try again.", "danger")
            return render_template("auth/register.html", form=form)

        # Create profile record
        if form.role.data == "Student":
            profile = Student(
                user_id=user.user_id,
                school=form.school.data,
                program=form.program.data,
                year_of_study=form.year_of_study.data,
                expected_graduation_year=form.expected_graduation_year.data,
                interests=form.interests.data
            )
        else:
            profile = Admin(
                user_id=user.user_id,
                staff_id=form.staff_id.data,
                department_name=form.department_name.data
            )
        db.session.add(profile)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash(
                "Failed to create user profile. Please contact support.",
                "danger",
            )
            return redirect(url_for("auth.register"))

        # Send confirmation email
        send_confirmation_email(user)
        flash(
            "Account created! A confirmation link has been sent to your email.",
            "success",
        )
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/confirm/<token>")
def confirm_email(token):
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))

    try:
        email = s.loads(token, salt="email-confirm", max_age=3600)
    except Exception:
        flash("That confirmation link is invalid or has expired.", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("No account found for that email.", "warning")
        return redirect(url_for("auth.register"))

    # Optional: mark user as confirmed
    # user.confirmed = True
    # db.session.commit()

    flash("Your email has been confirmed! You can now log in.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/reset_password", methods=["GET", "POST"])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))

    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        # Always send reset instructions (if user exists)
        if user:
            send_reset_email(user)
        flash(
            "If that email exists in our system, you’ll receive reset instructions shortly.",
            "info",
        )
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_request.html", form=form)


@auth_bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))

    try:
        email = s.loads(token, salt="password-reset", max_age=3600)
    except Exception:
        flash("That token is invalid or has expired.", "danger")
        return redirect(url_for("auth.reset_request"))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("auth.reset_request"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.password_hash = generate_password_hash(form.password.data)
        db.session.commit()
        flash("Your password has been updated! You can now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template(
        "auth/reset_token.html",
        form=form,
        token=token
    )


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
