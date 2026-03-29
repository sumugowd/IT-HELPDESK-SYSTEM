from flask import Blueprint , request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models.user import User

main = Blueprint('main', __name__)

# HOME
@main.route("/")
def home():
    return "IT Helpdesk System is Running"

# REGISTER
@main.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role")
    phone = data.get("phone")

    # Email Validation
    if not email.endswith("@atria.edu.in"):
        return jsonify({"error": "Only college emails allowed"}), 400
    
    # Check existing user
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "User already exists"}), 400
    
    # Hash password
    hashed_password = generate_password_hash(password)

    user = User(
        name = name,
        email = email,
        password = hashed_password,
        role = role,
        phone = phone
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"})

# Login
@main.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password,password):
        return jsonify({"error" : "Invalid credentials"}), 401
    
    # Store session
    session["user_id"] = user.id
    session["role"] = user.role

    return jsonify({
        "message": "Login successful",
        "role": user.role
    })

# Logout
@main.route("/logout")
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})