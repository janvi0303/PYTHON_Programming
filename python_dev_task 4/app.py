from flask import Flask, render_template, request, redirect, session, flash, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import re
from datetime import datetime

app = Flask(__name__)
app.secret_key = "cafe_secret_key_2024"

# Configure session
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'

TABLES = [1, 2, 3, 4, 5]
TIME_SLOTS = ["10:00-12:00", "12:00-14:00", "14:00-16:00", "16:00-18:00"]

# ---------------- DATABASE ---------------- #

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        # Users table with unique email constraint
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Bookings table with foreign key constraint
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                table_number INTEGER NOT NULL,
                date TEXT NOT NULL,
                time_slot TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(table_number, date, time_slot)
            )
        """)
        conn.commit()

# Initialize database
init_db()

# ---------------- PASSWORD VALIDATION ---------------- #

def validate_password(password):
    """Validate password with specific requirements"""
    errors = []
    
    if len(password) < 8:
        errors.append("At least 8 characters")
    
    if not re.search(r"\d", password):
        errors.append("At least 1 number")
    
    if not re.search(r"[A-Z]", password):
        errors.append("At least 1 uppercase letter")
    
    if not re.search(r"[a-z]", password):
        errors.append("At least 1 lowercase letter")
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        errors.append("At least 1 special character")
    
    return errors

# ---------------- HELPER FUNCTIONS ---------------- #

def get_today_date():
    """Get today's date in YYYY-MM-DD format"""
    return datetime.now().strftime("%Y-%m-%d")

# ---------------- ROUTES ---------------- #

@app.route("/")
def home():
    return redirect("/login")

# -------- REGISTER -------- #
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"].lower().strip()
        password = request.form["password"]
        
        # Email validation
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash("Invalid email format", "danger")
            return redirect("/register")
        
        # Password validation
        password_errors = validate_password(password)
        if password_errors:
            flash("Password requirements not met", "danger")
            for error in password_errors:
                flash(error, "warning")
            return redirect("/register")
        
        hashed_password = generate_password_hash(password)
        
        try:
            conn = get_db()
            # Check if email already exists
            existing_user = conn.execute(
                "SELECT id FROM users WHERE email = ?", (email,)
            ).fetchone()
            
            if existing_user:
                flash("Email already registered. Please login.", "warning")
                return redirect("/login")
            
            # Insert new user
            cursor = conn.execute(
                "INSERT INTO users (email, password) VALUES (?, ?)",
                (email, hashed_password)
            )
            conn.commit()
            
            # Get the new user
            user = conn.execute(
                "SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
            
            # Set session
            session["user_id"] = user["id"]
            session["email"] = user["email"]
            
            flash("Registration successful! Welcome to Cafe Booking.", "success")
            return redirect("/book")
            
        except sqlite3.Error as e:
            flash(f"Database error: {str(e)}", "danger")
            return redirect("/register")
    
    return render_template("register.html", page="register", today=get_today_date())

# -------- LOGIN -------- #
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].lower().strip()
        password = request.form["password"]
        
        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["email"] = user["email"]
            flash("Login successful!", "success")
            return redirect("/book")
        
        flash("Invalid email or password", "danger")
    
    return render_template("login.html", page="login", today=get_today_date())

# -------- BOOK TABLE -------- #
@app.route("/book", methods=["GET", "POST"])
def book():
    if "user_id" not in session:
        flash("Please login to book a table", "warning")
        return redirect("/login")
    
    conn = get_db()
    today = get_today_date()
    
    if request.method == "POST":
        try:
            table = int(request.form["table"])
            date = request.form["date"]
            time = request.form["time"]
            
            # Validate date is not in the past
            selected_date = datetime.strptime(date, "%Y-%m-%d").date()
            current_date = datetime.now().date()
            
            if selected_date < current_date:
                flash("Cannot book tables for past dates", "danger")
                return redirect("/book")
            
            # Check availability
            exists = conn.execute("""
                SELECT * FROM bookings 
                WHERE table_number = ? AND date = ? AND time_slot = ?
            """, (table, date, time)).fetchone()
            
            if exists:
                flash(f"Table {table} is already booked for {date} at {time}", "warning")
                return redirect("/book")
            
            # Create booking
            conn.execute("""
                INSERT INTO bookings (user_id, table_number, date, time_slot)
                VALUES (?, ?, ?, ?)
            """, (session["user_id"], table, date, time))
            conn.commit()
            
            flash(f"Table {table} booked successfully for {date} at {time}!", "success")
            return redirect("/my-bookings")
            
        except ValueError:
            flash("Invalid input data", "danger")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
    
    # Get all bookings for current date to show availability
    bookings = conn.execute("""
        SELECT table_number, date, time_slot FROM bookings 
        WHERE date >= ?
    """, (today,)).fetchall()
    
    return render_template(
        "book.html",
        tables=TABLES,
        times=TIME_SLOTS,
        bookings=bookings,
        page="book",
        today=today
    )

# -------- VIEW BOOKINGS -------- #
@app.route("/my-bookings")
def my_bookings():
    if "user_id" not in session:
        flash("Please login to view your bookings", "warning")
        return redirect("/login")
    
    conn = get_db()
    bookings = conn.execute("""
        SELECT * FROM bookings 
        WHERE user_id = ? 
        ORDER BY date DESC, time_slot ASC
    """, (session["user_id"],)).fetchall()
    
    today = get_today_date()
    return render_template("my_bookings.html", bookings=bookings, page="my-bookings", today=today)

# -------- CANCEL BOOKING -------- #
@app.route("/cancel/<int:booking_id>")
def cancel(booking_id):
    if "user_id" not in session:
        flash("Please login to cancel bookings", "warning")
        return redirect("/login")
    
    conn = get_db()
    
    # Verify ownership before deleting
    booking = conn.execute(
        "SELECT * FROM bookings WHERE id = ? AND user_id = ?",
        (booking_id, session["user_id"])
    ).fetchone()
    
    if not booking:
        flash("Booking not found or you don't have permission", "danger")
        return redirect("/my-bookings")
    
    conn.execute(
        "DELETE FROM bookings WHERE id = ? AND user_id = ?",
        (booking_id, session["user_id"])
    )
    conn.commit()
    
    flash("Booking cancelled successfully", "success")
    return redirect("/my-bookings")

# -------- LOGOUT -------- #
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "info")
    return redirect("/login")

# -------- API ENDPOINTS -------- #
@app.route("/api/availability")
def api_availability():
    date = request.args.get("date")
    if not date:
        return jsonify({"error": "Date parameter required"}), 400
    
    conn = get_db()
    data = []
    
    for table in TABLES:
        for time in TIME_SLOTS:
            booked = conn.execute("""
                SELECT * FROM bookings 
                WHERE table_number = ? AND date = ? AND time_slot = ?
            """, (table, date, time)).fetchone()
            
            data.append({
                "table": table,
                "time": time,
                "available": booked is None,
                "status": "Available" if booked is None else "Booked"
            })
    
    return jsonify({"date": date, "availability": data})

# ---------------- ERROR HANDLERS ---------------- #
@app.errorhandler(404)
def page_not_found(e):
    flash("Page not found", "warning")
    return redirect("/book")

@app.errorhandler(500)
def server_error(e):
    flash("Server error occurred", "danger")
    return redirect("/book")

# ---------------- MAIN ---------------- #
if __name__ == "__main__":
    app.run(debug=True)
