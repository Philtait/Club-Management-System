from flask import Flask, render_template, request, redirect , session , url_for ,flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = ""

# Configure SQL Alchemy
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///cms.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Database Model
class User(db.Model):
    # Class Variables
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(50), nullable=False)
    first_name = db.Column(db.String(50))
    middle_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    gender = db.Column(db.String(10))
    email = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(255), nullable=False)

    # Student-specific fields
    faculty = db.Column(db.String(100))
    course_level = db.Column(db.String(50))
    course_name = db.Column(db.String(100))
    year_of_study = db.Column(db.String(10))
    expected_completion = db.Column(db.String(10))
    interests = db.Column(db.String(100))

    # Staff-specific fields
    staff_id = db.Column(db.String(50))
    department = db.Column(db.String(100))

    # Club Leader-specific fields
    club_category = db.Column(db.String(100))
    club_name = db.Column(db.String(100))
    club_role = db.Column(db.String(100))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password) 
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Routes
@app.route("/")
def home():
    if "username" in session:
        return redirect(url_for('dashboard'))
    return render_template("SignUp.html")

# Register
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        role = request.form["role"]
        first_name = request.form["first_name"]
        middle_name = request.form["middle_name"]
        last_name = request.form["last_name"]
        gender = request.form["gender"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]

        # Role-specific fields
        faculty = request.form.get("faculty")
        course_level = request.form.get("course_level")
        course_name = request.form.get("course_name")
        year_of_study = request.form.get("year_of_study")
        expected_completion = request.form.get("expected_completion")
        interests = request.form.get("interests")
        staff_id = request.form.get("staff_id")
        department = request.form.get("department")
        club_name = request.form.get("club_name")
        club_category = request.form.get("club_category")
        club_role = request.form.get("club_role")

        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered. Please login.", "warning")
            return redirect(url_for("login"))

        # Create new user
        new_user = User(
            role=role,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            gender=gender,
            email=email,
            phone=phone,
            faculty=faculty,
            course_level=course_level,
            course_name=course_name,
            year_of_study=year_of_study,
            expected_completion=expected_completion,
            interests=interests,
            staff_id=staff_id,
            department=department,
            club_name=club_name,
            club_category=club_category,
            club_role=club_role
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            session["username"] = user.first_name  # optional
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password. Please try again.", "danger")
            return redirect(url_for("index.html"))

    return render_template("login.html")

# Dashboard
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])
    return render_template("dashboard.html", user=user)

# Logout
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))




if __name__ in "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)