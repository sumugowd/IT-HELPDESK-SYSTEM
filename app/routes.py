from flask import Blueprint , request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models.user import User
from app.models.ticket import Ticket

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

# Create Ticket
@main.route("/create-ticket", methods=["POST"])
def create_ticket():
    # Check login
    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401
    
    # Only staff allowed
    if session.get("role") != "staff":
        return jsonify({"error": "Only staff can create tickets"}), 403
    
    data = request.get_json()

    title = data.get("title")
    description = data.get("description")
    issue_type = data.get("issue_type")
    location = data.get("location")
    phone = data.get("phone")

    # Basic validation
    if not all([title, description, issue_type, location, phone]):
        return jsonify({"error": "All fields are required"}), 400
    
    ticket = Ticket(
        title = title,
        description = description,
        issue_type = issue_type,
        location = location,
        created_by = session["user_id"],
        phone = phone
    )

    db.session.add(ticket)
    db.session.commit()

    return jsonify({
        "message": "Ticket created successfully",
        "ticket_id" : ticket.id
    })