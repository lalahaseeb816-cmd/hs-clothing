from flask import Flask, request, session, render_template, redirect
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)

app.secret_key = "h&s-clothing-secret-key"

CORS(app)


# =========================
# DATABASE
# =========================

def get_db():
    conn = sqlite3.connect("hs_clothing.db")
    conn.row_factory = sqlite3.Row
    return conn
    
    @app.route("/")
def home():
    return render_template("index.html")


def create_database():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            category TEXT NOT NULL,
            style TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0
        )
    """)

    conn.commit()

    conn.close()


# =========================
# WEBSITE
# =========================

@app.route("/")
def home():
    return render_template("index.html")


# =========================
# ADMIN LOGIN
# =========================

@app.route("/admin-login")
def admin_login_page():
    return render_template("admin_login.html")


@app.route("/admin")
def admin():

    if "admin_id" not in session:
        return redirect("/admin-login")

    return render_template("admin.html")


@app.route("/api/admin/login", methods=["POST"])
def admin_login():

    data = request.get_json()

    email = data.get("email", "").strip()
    password = data.get("password", "")

    conn = get_db()

    admin = conn.execute(
        "SELECT * FROM users WHERE email = ? AND is_admin = 1",
        (email,)
    ).fetchone()

    conn.close()

    if admin is None:
        return {"error": "Invalid email or password"}, 401

    if not check_password_hash(
        admin["password_hash"],
        password
    ):
        return {"error": "Invalid email or password"}, 401

    session["admin_id"] = admin["id"]
    session["admin_email"] = admin["email"]

    return {
        "message": "Login successful"
    }, 200


@app.route("/api/admin/logout", methods=["POST"])
def admin_logout():

    session.pop("admin_id", None)
    session.pop("admin_email", None)

    return {
        "message": "Logged out successfully"
    }, 200


# =========================
# PRODUCTS - GET
# =========================

@app.route("/api/products", methods=["GET"])
def products():

    conn = get_db()

    rows = conn.execute(
        "SELECT * FROM products"
    ).fetchall()

    conn.close()

    product_list = []

    for row in rows:

        product_list.append({
            "id": row["id"],
            "name": row["name"],
            "price": row["price"],
            "category": row["category"],
            "style": row["style"]
        })

    return {
        "products": product_list
    }


# =========================
# PRODUCTS - ADD
# =========================

@app.route("/api/products", methods=["POST"])
def add_product():

    data = request.get_json()

    name = data.get("name", "").strip()
    category = data.get("category", "").strip()
    price = data.get("price")

    if not name or not category or price is None:

        return {
            "error": "All fields are required"
        }, 400

    conn = get_db()

    try:

        conn.execute("""
            INSERT INTO products
            (name, price, category)
            VALUES (?, ?, ?)
        """, (
            name,
            float(price),
            category
        ))

        conn.commit()

    finally:

        conn.close()

    return {
        "message": "Product added successfully"
    }, 201


# =========================
# CREATE ADMIN
# =========================

def create_admin():

    conn = get_db()

    existing_admin = conn.execute(
        "SELECT * FROM users WHERE email = ?",
        ("admin@hsclothing.com",)
    ).fetchone()

    if existing_admin is None:

        password_hash = generate_password_hash(
            "Admin@12345"
        )

        conn.execute("""
            INSERT INTO users
            (name, email, password_hash, is_admin)
            VALUES (?, ?, ?, 1)
        """, (
            "H&S Admin",
            "admin@hsclothing.com",
            password_hash
        ))

        conn.commit()

    conn.close()


# =========================
# START SERVER
# =========================

if __name__ == "__main__":

    create_database()

    create_admin()

    app.run(debug=True)
