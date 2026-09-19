import os
import sqlite3
from functools import wraps

from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    session,
    redirect
)
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash


# ============================================================
# APP CONFIGURATION
# ============================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "development-secret-change-this"
)

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = (
    os.environ.get("SESSION_COOKIE_SECURE", "true").lower() == "true"
)

CORS(app, supports_credentials=True)


# ============================================================
# DATABASE
# ============================================================

DATABASE = os.environ.get(
    "DATABASE_PATH",
    "hands_clothing.db"
)


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_database():

    db = get_db()

    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            type TEXT,
            price REAL NOT NULL,
            image TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            order_data TEXT NOT NULL,
            total REAL DEFAULT 0,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
            REFERENCES users(id)
        )
    """)

    db.commit()

    product_count = db.execute(
        "SELECT COUNT(*) FROM products"
    ).fetchone()[0]

    if product_count == 0:

        initial_products = [

            (
                "Classic Black Suit",
                "Men",
                "Formal",
                4999,
                "https://images.unsplash.com/photo-1598808503746-f34c53b9323e?auto=format&fit=crop&w=800&q=80"
            ),

            (
                "Premium White Shirt",
                "Men",
                "Formal",
                1499,
                "https://images.unsplash.com/photo-1603252110481-7ba873bf42ab?auto=format&fit=crop&w=800&q=80"
            ),

            (
                "Luxury Black Dress",
                "Women",
                "Formal",
                3999,
                "https://images.unsplash.com/photo-1566174053879-31528523f8ae?auto=format&fit=crop&w=800&q=80"
            ),

            (
                "Streetwear Hoodie",
                "Men",
                "Streetwear",
                1999,
                "https://images.unsplash.com/photo-1556821840-3a63f95609a7?auto=format&fit=crop&w=800&q=80"
            ),

            (
                "Women's Casual Outfit",
                "Women",
                "Casual",
                2499,
                "https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=800&q=80"
            ),

            (
                "Premium Blazer",
                "Men",
                "Formal",
                5499,
                "https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&w=800&q=80"
            ),

            (
                "Elegant Women's Dress",
                "Women",
                "Party",
                3499,
                "https://images.unsplash.com/photo-1595777457583-95e059d581b8?auto=format&fit=crop&w=800&q=80"
            ),

            (
                "Urban Streetwear",
                "Men",
                "Streetwear",
                2299,
                "https://images.unsplash.com/photo-1529139574466-a303027c1d8b?auto=format&fit=crop&w=800&q=80"
            )
        ]

        db.executemany("""
            INSERT INTO products
            (name, category, type, price, image)
            VALUES (?, ?, ?, ?, ?)
        """, initial_products)

        db.commit()

    db.close()


# ============================================================
# ADMIN AUTHENTICATION
# ============================================================

def admin_required(function):

    @wraps(function)
    def decorated_function(*args, **kwargs):

        if not session.get("admin_logged_in"):
            return jsonify({
                "error": "Admin authentication required"
            }), 401

        return function(*args, **kwargs)

    return decorated_function


# ============================================================
# CUSTOMER AUTHENTICATION
# ============================================================

def user_required(function):

    @wraps(function)
    def decorated_function(*args, **kwargs):

        if not session.get("user_id"):
            return jsonify({
                "error": "Login required"
            }), 401

        return function(*args, **kwargs)

    return decorated_function


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():
    return render_template("index.html")


# ============================================================
# ADMIN LOGIN PAGE
# ============================================================

@app.route("/admin-login")
def admin_login_page():
    return render_template("admin-login.html")


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route("/admin")
def admin_dashboard():

    if not session.get("admin_logged_in"):
        return redirect("/admin-login")

    return render_template("admin.html")


# ============================================================
# ADMIN LOGIN API
# ============================================================

@app.route("/api/admin/login", methods=["POST"])
def admin_login():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "No data received"
        }), 400

    username = str(
        data.get("username", "")
    ).strip()

    password = str(
        data.get("password", "")
    )

    admin_username = os.environ.get(
        "ADMIN_USERNAME",
        "admin"
    )

    admin_password_hash = os.environ.get(
        "ADMIN_PASSWORD_HASH",
        ""
    ).strip()

    if not admin_password_hash:

        return jsonify({
            "error": "Admin credentials are not configured on the server"
        }), 500

    try:
        password_valid = check_password_hash(
            admin_password_hash,
            password
        )
    except Exception:

        return jsonify({
            "error": "Invalid password hash configuration"
        }), 500

    if username != admin_username or not password_valid:

        return jsonify({
            "error": "Invalid admin username or password"
        }), 401

    session.clear()

    session["admin_logged_in"] = True
    session["admin_username"] = admin_username

    return jsonify({
        "message": "Admin login successful"
    })


# ============================================================
# ADMIN LOGOUT
# ============================================================

@app.route("/api/admin/logout", methods=["POST"])
def admin_logout():

    session.pop("admin_logged_in", None)
    session.pop("admin_username", None)

    return jsonify({
        "message": "Admin logged out"
    })


# ============================================================
# CHECK ADMIN SESSION
# ============================================================

@app.route("/api/admin/me")
def admin_me():

    if not session.get("admin_logged_in"):

        return jsonify({
            "logged_in": False
        }), 401

    return jsonify({
        "logged_in": True,
        "username": session.get("admin_username")
    })


# ============================================================
# PRODUCTS - GET
# ============================================================

@app.route("/api/products", methods=["GET"])
def get_products():

    db = get_db()

    rows = db.execute("""
        SELECT
            id,
            name,
            category,
            type,
            price,
            image
        FROM products
        ORDER BY id
    """).fetchall()

    db.close()

    return jsonify({
        "products": [
            dict(row)
            for row in rows
        ]
    })


# ============================================================
# SINGLE PRODUCT
# ============================================================

@app.route("/api/products/<int:product_id>", methods=["GET"])
def get_product(product_id):

    db = get_db()

    row
