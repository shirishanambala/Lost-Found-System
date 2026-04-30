from flask import Flask, render_template, request, redirect, url_for, session, flash,jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# -------------------------------
# DATABASE SETUP
# -------------------------------
def init_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row  # <-- Add this

    c = conn.cursor()
    
    # Users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    
    # Items table (lost/found reports)
    c.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            kind TEXT,
            title TEXT,
            category TEXT,
            date TEXT,
            description TEXT,
            location TEXT,
            image TEXT,
            contact_email TEXT,      -- NEW
            contact_phone TEXT,      -- NEW
            status TEXT DEFAULT 'Pending'
        )
    """)
    
    # Claims table
    # Claims table
    c.execute("""
    CREATE TABLE IF NOT EXISTS claims (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER,
        claimant_email TEXT,
        message TEXT,
        status TEXT DEFAULT 'Pending',
        user_reply TEXT
    )
""")

    
    conn.commit()
    conn.close()

init_db()

# -------------------------------
# USER SIGNUP
# -------------------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        try:
            conn = sqlite3.connect("database.db")
            c = conn.cursor()
            c.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
            conn.commit()
            conn.close()

            # Auto-login
            session["user"] = email
            flash("Signup successful! You are now logged in.", "success")
            return redirect(url_for("user_dashboard"))
        except sqlite3.IntegrityError:
            flash("Email already exists!", "error")
            return redirect(url_for("signup"))
    return render_template("signup.html")

# -------------------------------
# USER LOGIN
# -------------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = c.fetchone()
        conn.close()

        if user:
            session["user"] = email
            return redirect(url_for("user_dashboard"))
        else:
            flash("Invalid login details", "error")
    return render_template("index.html")

# -------------------------------
# USER DASHBOARD
# -------------------------------
@app.route("/dashboard")
def user_dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    user_email = session["user"]

    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Stats
    c.execute("SELECT COUNT(*) FROM items WHERE kind='Lost' AND user_email=?", (user_email,))
    lost_count = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM items WHERE kind='Found' AND user_email=?", (user_email,))
    found_count = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM claims WHERE claimant_email=?", (user_email,))
    claims_count = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM items WHERE user_email=?", (user_email,))
    total_count = c.fetchone()[0]

    # 🆕 Fetch all items (Lost + Found)
    c.execute("SELECT id, kind, title, category, date, description, location, image FROM items ORDER BY id DESC")

    items = c.fetchall()
# Fetch user’s own claims

    c.execute("""
    SELECT claims.id AS claim_id, claims.item_id, claims.message, claims.status AS claim_status,
           items.title, items.location, items.description, items.contact_email, items.contact_phone
    FROM claims
    JOIN items ON claims.item_id = items.id
    WHERE claims.claimant_email = ?
    ORDER BY claims.id DESC
""", (user_email,))
    user_claims = c.fetchall()

    conn.close()

    return render_template("user_dashboard.html",
                       user=user_email,
                       lost_count=lost_count,
                       found_count=found_count,
                       claims_count=claims_count,
                       total_count=total_count,
                       items=items,
                       user_claims=user_claims)  # <-- add this

# -------------------------------
# BROWSE ITEMS
# -------------------------------
@app.route("/browse")
def browse_items():
    if "user" not in session:
        return redirect(url_for("login"))

    search = request.args.get("search", "").strip().lower()
    category = request.args.get("category", "").strip()

    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row  # Safe dict-like access
    c = conn.cursor()

    # Build SQL query based on search and category
    if search and category:
        query = f"%{search}%"
        c.execute("""
            SELECT * FROM items 
            WHERE (LOWER(title) LIKE ? OR LOWER(description) LIKE ? OR LOWER(location) LIKE ?) 
              AND category=? 
            ORDER BY id DESC
        """, (query, query, query, category))
    elif search:
        query = f"%{search}%"
        c.execute("""
            SELECT * FROM items 
            WHERE LOWER(title) LIKE ? OR LOWER(description) LIKE ? OR LOWER(location) LIKE ? 
            ORDER BY id DESC
        """, (query, query, query))
    elif category:
        c.execute("SELECT * FROM items WHERE category=? ORDER BY id DESC", (category,))
    else:
        c.execute("SELECT * FROM items ORDER BY id DESC")

    items = c.fetchall()
    conn.close()

    return render_template("user_dashboard.html", items=items, search=search, category=category)



# -------------------------------
# REPORT LOST/FOUND ITEM
# -------------------------------
@app.route("/report-item", methods=["POST"])
def report_item():
    if "user" not in session:
        return redirect(url_for("login"))

    user_email = session["user"]
    kind = request.form["kind"]
    title = request.form["title"]
    category = request.form["category"]
    date = request.form["date"]
    description = request.form["description"]
    location = request.form["location"]
    contact_email = request.form["contact_email"]
    contact_phone = request.form["contact_phone"]

    # ✅ Validation
    year = date.split("-")[0]
    current_year = datetime.now().year

    if not location.replace(" ", "").isalpha():
        flash("❌ Please enter a valid location (letters only).", "error")
        return redirect(url_for("user_dashboard"))

    if not year.isdigit() or int(year) > current_year:
        flash("⚠️ Please enter a valid year (not in the future).", "error")
        return redirect(url_for("user_dashboard"))

    # ✅ Image Handling
    image_file = request.files.get("image")
    image_filename = None
    if image_file and allowed_file(image_file.filename):
        image_filename = secure_filename(image_file.filename)
        image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], image_filename))

    # ✅ Database Save
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO items (user_email, kind, title, category, date, description, location, image, contact_email, contact_phone)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_email, kind, title, category, date, description, location, image_filename, contact_email, contact_phone))
    conn.commit()
    conn.close()

    flash(f"{kind} item reported successfully!", "success")
    return redirect(url_for("user_dashboard"))

@app.route("/submit-claim", methods=["POST"])
def submit_claim():
    if "user" not in session:
        return redirect(url_for("login"))

    claimant_email = session["user"]
    item_id = request.form["item_id"]
    message = request.form["message"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("INSERT INTO claims (item_id, claimant_email, message) VALUES (?, ?, ?)",
              (item_id, claimant_email, message))
    conn.commit()
    conn.close()

    flash("Your claim has been submitted!", "success")
    return redirect(url_for("user_dashboard"))
@app.route('/reply-claim', methods=['POST'])
def reply_claim():
    claim_id = request.form['claim_id']
    reply_message = request.form['replyMessage']

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # Assuming you have a column 'user_reply' in your claims table
    cursor.execute("UPDATE claims SET user_reply = ? WHERE id = ?", (reply_message, claim_id))
    conn.commit()
    conn.close()

    flash("Your message has been sent to admin.", "success")
    return redirect(url_for('user_dashboard'))

# -------------------------------
# ADMIN LOGIN (dummy)
# -------------------------------
@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # Dummy admin credentials
        if email == "admin@test.com" and password == "admin123":
            session["admin"] = email
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid admin credentials", "error")
    return render_template("admin_login.html")

# -------------------------------
# ADMIN DASHBOARD
# -------------------------------
@app.route("/admin-dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Join claims with items table twice — once for lost, once for found
    c.execute("""
    SELECT 
        claims.id AS claim_id,
        claims.message AS claim_message,
        claims.status,      -- <-- keep it as 'status'
        claims.user_reply,

        lost.id AS lost_item_id,
        lost.kind AS lost_kind,
        lost.title AS lost_title,
        lost.category AS lost_category,
        lost.date AS lost_date,
        lost.description AS lost_description,
        lost.location AS lost_location,
        lost.image AS lost_image,
        lost.contact_email AS lost_contact_email,
        lost.contact_phone AS lost_contact_phone,

        found.description AS found_report

    FROM claims
    JOIN items AS lost ON claims.item_id = lost.id
    LEFT JOIN items AS found ON found.kind = 'Found' 
                               AND found.category = lost.category
                               AND found.location = lost.location
    ORDER BY claims.id DESC
""")

    claims = c.fetchall()
    conn.close()

    return render_template("admin_dashboard.html",
                           admin=session["admin"],
                           claims=claims)
@app.route("/approve_claim/<int:claim_id>")
def approve_claim(claim_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("UPDATE claims SET status = 'Approved' WHERE id = ?", (claim_id,))
    conn.commit()
    conn.close()
    flash("Claim approved successfully!")
    return redirect(url_for("admin_dashboard"))

@app.route("/reject_claim/<int:claim_id>")
def reject_claim(claim_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("UPDATE claims SET status = 'Rejected' WHERE id = ?", (claim_id,))
    conn.commit()
    conn.close()
    flash("Claim rejected successfully!")
    return redirect(url_for("admin_dashboard"))

@app.route('/update-status/<int:claim_id>', methods=['POST'])
def update_status(claim_id):
    data = request.get_json()
    status = data.get('status')

    # --- Update your database here ---
    # Example (uncomment and adapt for your DB):
    # conn = sqlite3.connect('your_db.db')
    # cursor = conn.cursor()
    # cursor.execute("UPDATE claims SET status=? WHERE claim_id=?", (status, claim_id))
    # conn.commit()
    # conn.close()

    return jsonify({"success": True})





@app.route('/request-info', methods=['POST'])
def request_info():
    claim_id = request.form.get('claim_id')
    message = request.form.get('message')
    if claim_id and message:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        # ✅ Use "id" instead of "claim_id"
        c.execute("UPDATE claims SET message=?, status='Need Info' WHERE id=?", (message, claim_id))
        conn.commit()
        conn.close()
        flash('ℹ️ Request for more info sent successfully.', 'success')
    else:
        flash('❌ Something went wrong. Please try again.', 'error')
    return redirect(url_for('admin_dashboard'))






# -------------------------------
# LOGOUT
# -------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# -------------------------------
# RUN APP
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True) 
