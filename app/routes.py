from flask import Blueprint , request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models.user import User
from app.models.ticket import Ticket
from app.models.user import User
from app.models.notification import Notification

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

    notification = Notification(
        user_id = session["user_id"],
        message = f"Ticket '{title}' created successfully"
    )

    return jsonify({
        "message": "Ticket created successfully",
        "ticket_id" : ticket.id
    })

# View Open Tickets(Technician & Head)
@main.route("/tickets", methods=["GET"])
def view_tickets():
    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401
    
    if session.get("role") not in ["technician", "head"]:
        return jsonify({"error": "Access denied"}), 403
    
    tickets = Ticket.query.filter_by(status="Open").all()

    result = []
    for t in tickets:
        result.append({
            "id": t.id,
            "title": t.title,
            "issue_type": t.issue_type,
            "location": t.location,
            "status": t.status
        })

    return jsonify(result)

# Pick Ticket (Technician) 
@main.route("/pick-ticket/<int:ticket_id>", methods=["POST"])
def pick_ticket(ticket_id):
    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401
    
    if session.get("role") != "technician":
        return jsonify({"error": "Only technician can pick tickets"}), 403
    
    technician_id = session["user_id"]

    # Check if technician already has active ticket
    existing_ticket = Ticket.query.filter(
        Ticket.assigned_to == technician_id,
        Ticket.status.in_(["Assigned", "In Progress"])
    ).first()

    if existing_ticket:
        return jsonify({"error": "You already have an active ticket"}), 400
    
    # Get ticket
    ticket = Ticket.query.get(ticket_id)

    if not ticket:
        return jsonify({"error": "Ticket not found"}), 404
    
    if ticket.status != "Open":
        return jsonify({"error": "Ticket already taken"}), 400
    
    # Assign ticket
    ticket.assigned_to = technician_id
    ticket.status = "Assigned"

    db.session.commit()

    # Notify technician
    notif1 = Notification(
        user_id=technician_id,
        message=f"You have been assigned ticket #{ticket.id}"
    )

    # Nofify staff
    notif2 = Notification(
        user_id=ticket.created_by,
        message=f"Your ticket #{ticket.id} has been assigned"
    )

    db.session.add_all([notif1, notif2])

    return jsonify({
        "message": "Ticket assigned successfully",
        "ticket_id": ticket.id
    })

# Update Ticket status
@main.route("/update-ticket/<int:ticket_id>", methods=["POST"])
def update_ticket(ticket_id):
    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401
    
    data = request.get_json()
    new_status = data.get("status")

    ticket = Ticket.query.get(ticket_id)

    if not ticket:
        return jsonify({"error": "Ticket not found"}), 404
    
    user_id = session["user_id"]
    role = session["role"]

    # Technician updates
    if role == "technician":
        if ticket.assigned_to != user_id:
            return jsonify({"error": "Not your ticket"}), 403
        
        if ticket.status == "Assigned" and new_status == "In Progress":
            ticket.status = "In Progress"

        elif ticket.status == "In Progress" and new_status == "Resolved":
            ticket.status = "Resolved"

        else:
            return jsonify({"error": "Invalid status transition"}), 400
        
    # Staff closes ticket
    elif role == "staff":
        if ticket.created_by != user_id:
            return jsonify({"error": "Not your ticket"}), 403
        
        if ticket.status == "Resolved" and new_status == "Closed":
            ticket.status = "Closed"
        else:
            return jsonify({"error": "Invalid status transition"}), 400
        
    else:
        return jsonify({"error": "Access denied"}), 403
    
    notif = Notification(
        user_id = ticket.created_by,
        message=f"Ticket #{ticket.id} status updated to {ticket.status}"
    )

    db.session.add(notif)
    
    # Only commit if everything valid
    db.session.commit()

    return jsonify({
        "message": "Ticket updated",
        "new_status": ticket.status
    })

# View My Tickets (Staff)
@main.route("/my-tickets", methods=["GET"])
def my_tickets():
    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401
    
    if session.get("role") != "staff":
        return jsonify({"error": "Access denied"}), 403
    
    tickets = Ticket.query.filter_by(created_by=session["user_id"]).all()
    
    result = []
    for t in tickets:
        technician = None

        if t.assigned_to:
            technician = User.query.get(t.assigned_to)

        
        result.append({
            "id": t.id,
            "title": t.title,
            "status": t.status,
            "issue_type": t.issue_type,
            "location": t.location,

            # Technician details
            "technician_name": technician.name if technician else None,
            "technician_phone": technician.phone if technician else None
        })

    return jsonify(result)

# View My Assigned Tickets (Technician)
@main.route("/assigned-tickets", methods=["GET"])
def assigned_tickets():
    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401
    
    if session.get("role") != "technician":
        return jsonify({"error": "Access denied"}), 403
    
    tickets = Ticket.query.filter_by(assigned_to=session["user_id"]).all()

    result = []
    for t in tickets:
        staff = User.query.get(t.created_by)

        result.append({
            "id": t.id,
            "title": t.title,
            "status": t.status,
            "issue_type": t.issue_type,
            "location": t.location,

            # Staff details
            "staff_name": staff.name,
            "staff_phone": staff.phone
        })

    return jsonify(result)

# Get Notifications
@main.route("/notifications", methods=["GET"])
def get_notifications():
    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401
    
    notifications = Notification.query.filter_by(
        user_id=session["user_id"]
    ).order_by(Notification.created_at.desc()).all()

    result = []
    for n in notifications:
        result.append({
            "id": n.id,
            "message": n.message,
            "is_read": n.is_read
        })

    return jsonify(result)