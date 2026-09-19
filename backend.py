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

CORS(
    app,
    supports_credentials=True
)


# ============================================================
# ADMIN CREDENTIALS
# ============================================================

ADMIN_USERNAME = "lalahaseeb@816gmail.com"
ADMIN_PASSWORD = "Haseeb12000"


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

    # Users
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Products
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

    # Orders
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

    # Add initial products if database is empty
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

    if (
        username != ADMIN_USERNAME
        or password != ADMIN_PASSWORD
    ):

        return jsonify({
            "error": "Invalid admin username or password"
        }), 401

    session.clear()

    session["admin_logged_in"] = True
    session["admin_username"] = ADMIN_USERNAME

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

    row = db.execute("""
        SELECT
            id,
            name,
            category,
            type,
            price,
            image
        FROM products
        WHERE id = ?
    """, (product_id,)).fetchone()

    db.close()

    if row is None:

        return jsonify({
            "error": "Product not found"
        }), 404

    return jsonify(dict(row))


# ============================================================
# ADMIN - ADD PRODUCT
# ============================================================

@app.route("/api/products", methods=["POST"])
@admin_required
def add_product():

    data = request.get_json(silent=True)

    if not data:

        return jsonify({
            "error": "No product data received"
        }), 400

    name = str(
        data.get("name", "")
    ).strip()

    category = str(
        data.get("category", "")
    ).strip()

    product_type = str(
        data.get("type", "")
    ).strip()

    image = str(
        data.get("image", "")
    ).strip()

    try:

        price = float(
            data.get("price")
        )

    except (TypeError, ValueError):

        return jsonify({
            "error": "Invalid price"
        }), 400

    if not name or not category:

        return jsonify({
            "error": "Product name and category are required"
        }), 400

    if price < 0:

        return jsonify({
            "error": "Price cannot be negative"
        }), 400

    db = get_db()

    cursor = db.execute("""
        INSERT INTO products
        (name, category, type, price, image)
        VALUES (?, ?, ?, ?, ?)
    """, (
        name,
        category,
        product_type,
        price,
        image
    ))

    db.commit()

    product_id = cursor.lastrowid

    db.close()

    return jsonify({
        "message": "Product added successfully",
        "product": {
            "id": product_id,
            "name": name,
            "category": category,
            "type": product_type,
            "price": price,
            "image": image
        }
    }), 201


# ============================================================
# ADMIN - UPDATE PRODUCT
# ============================================================

@app.route("/api/products/<int:product_id>", methods=["PUT"])
@admin_required
def update_product(product_id):

    data = request.get_json(silent=True)

    if not data:

        return jsonify({
            "error": "No product data received"
        }), 400

    name = str(
        data.get("name", "")
    ).strip()

    category = str(
        data.get("category", "")
    ).strip()

    product_type = str(
        data.get("type", "")
    ).strip()

    image = str(
        data.get("image", "")
    ).strip()

    try:

        price = float(
            data.get("price")
        )

    except (TypeError, ValueError):

        return jsonify({
            "error": "Invalid price"
        }), 400

    if not name or not category:

        return jsonify({
            "error": "Name and category are required"
        }), 400

    db = get_db()

    existing = db.execute(
        "SELECT id FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()

    if existing is None:

        db.close()

        return jsonify({
            "error": "Product not found"
        }), 404

    db.execute("""
        UPDATE products
        SET
            name = ?,
            category = ?,
            type = ?,
            price = ?,
            image = ?
        WHERE id = ?
    """, (
        name,
        category,
        product_type,
        price,
        image,
        product_id
    ))

    db.commit()
    db.close()

    return jsonify({
        "message": "Product updated successfully"
    })


# ============================================================
# ADMIN - DELETE PRODUCT
# ============================================================

@app.route("/api/products/<int:product_id>", methods=["DELETE"])
@admin_required
def delete_product(product_id):

    db = get_db()

    cursor = db.execute(
        "DELETE FROM products WHERE id = ?",
        (product_id,)
    )

    db.commit()

    deleted = cursor.rowcount

    db.close()

    if deleted == 0:

        return jsonify({
            "error": "Product not found"
        }), 404

    return jsonify({
        "message": "Product deleted successfully"
    })


# ============================================================
# CUSTOMER REGISTRATION
# ============================================================

@app.route("/api/register", methods=["POST"])
def register():

    data = request.get_json(silent=True)

    if not data:

        return jsonify({
            "error": "No data received"
        }), 400

    name = str(
        data.get("name", "")
    ).strip()

    email = str(
        data.get("email", "")
    ).strip().lower()

    password = str(
        data.get("password", "")
    )

    if not name or not email or not password:

        return jsonify({
            "error": "Name, email and password are required"
        }), 400

    if len(password) < 8:

        return jsonify({
            "error": "Password must contain at least 8 characters"
        }), 400

    db = get_db()

    existing = db.execute(
        "SELECT id FROM users WHERE email = ?",
        (email,)
    ).fetchone()

    if existing:

        db.close()

        return jsonify({
            "error": "Email already registered"
        }), 409

    password_hash = generate_password_hash(password)

    cursor = db.execute("""
        INSERT INTO users
        (name, email, password)
        VALUES (?, ?, ?)
    """, (
        name,
        email,
        password_hash
    ))

    db.commit()

    user_id = cursor.lastrowid

    db.close()

    session.clear()

    session["user_id"] = user_id
    session["user_name"] = name
    session["user_email"] = email

    return jsonify({
        "message": "Registration successful",
        "user": {
            "id": user_id,
            "name": name,
            "email": email
        }
    }), 201


# ============================================================
# CUSTOMER LOGIN
# ============================================================

@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json(silent=True)

    if not data:

        return jsonify({
            "error": "No data received"
        }), 400

    email = str(
        data.get("email", "")
    ).strip().lower()

    password = str(
        data.get("password", "")
    )

    db = get_db()

    user = db.execute("""
        SELECT
            id,
            name,
            email,
            password
        FROM users
        WHERE email = ?
    """, (email,)).fetchone()

    db.close()

    if not user:

        return jsonify({
            "error": "Invalid email or password"
        }), 401

    if not check_password_hash(
        user["password"],
        password
    ):

        return jsonify({
            "error": "Invalid email or password"
        }), 401

    session.clear()

    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    session["user_email"] = user["email"]

    return jsonify({
        "message": "Login successful",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"]
        }
    })


# ============================================================
# CUSTOMER LOGOUT
# ============================================================

@app.route("/api/logout", methods=["POST"])
def logout():

    session.clear()

    return jsonify({
        "message": "Logged out successfully"
    })


# ============================================================
# CURRENT CUSTOMER
# ============================================================

@app.route("/api/me")
def current_user():

    if not session.get("user_id"):

        return jsonify({
            "logged_in": False
        }), 401

    return jsonify({
        "logged_in": True,
        "user": {
            "id": session.get("user_id"),
            "name": session.get("user_name"),
            "email": session.get("user_email")
        }
    })


# ============================================================
# CREATE ORDER
# ============================================================

@app.route("/api/orders", methods=["POST"])
@user_required
def create_order():

    data = request.get_json(silent=True)

    if not data:

        return jsonify({
            "error": "No order data received"
        }), 400

    order_data = str(
        data.get("order_data", data)
    )

    try:

        total = float(
            data.get("total", 0)
        )

    except (TypeError, ValueError):

        total = 0

    db = get_db()

    cursor = db.execute("""
        INSERT INTO orders
        (user_id, order_data, total)
        VALUES (?, ?, ?)
    """, (
        session["user_id"],
        order_data,
        total
    ))

    db.commit()

    order_id = cursor.lastrowid

    db.close()

    return jsonify({
        "message": "Order created successfully",
        "order_id": order_id
    }), 201


# ============================================================
# CUSTOMER ORDERS
# ============================================================

@app.route("/api/my-orders")
@user_required
def my_orders():

    db = get_db()

    rows = db.execute("""
        SELECT
            id,
            order_data,
            total,
            status,
            created_at
        FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
    """, (
        session["user_id"],
    )).fetchall()

    db.close()

    return jsonify({
        "orders": [
            dict(row)
            for row in rows
        ]
    })


# ============================================================
# ADMIN - ORDERS
# ============================================================

@app.route("/api/admin/orders")
@admin_required
def admin_orders():

    db = get_db()

    rows = db.execute("""
        SELECT
            orders.id,
            orders.order_data,
            orders.total,
            orders.status,
            orders.created_at,
            users.name,
            users.email
        FROM orders
        LEFT JOIN users
        ON orders.user_id = users.id
        ORDER BY orders.id DESC
    """).fetchall()

    db.close()

    return jsonify({
        "orders": [
            dict(row)
            for row in rows
        ]
    })


# ============================================================
# ADMIN - CUSTOMERS
# ============================================================

@app.route("/api/admin/customers")
@admin_required
def admin_customers():

    db = get_db()

    rows = db.execute("""
        SELECT
            id,
            name,
            email,
            created_at
        FROM users
        ORDER BY id DESC
    """).fetchall()

    db.close()

    return jsonify({
        "customers": [
            dict(row)
            for row in rows
        ]
    })


# ============================================================
# ADMIN - DASHBOARD STATISTICS
# ============================================================

@app.route("/api/admin/stats")
@admin_required
def admin_stats():

    db = get_db()

    products_count = db.execute(
        "SELECT COUNT(*) FROM products"
    ).fetchone()[0]

    customers_count = db.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone()[0]

    orders_count = db.execute(
        "SELECT COUNT(*) FROM orders"
    ).fetchone()[0]

    sales = db.execute(
        "SELECT COALESCE(SUM(total), 0) FROM orders"
    ).fetchone()[0]

    db.close()

    return jsonify({
        "products": products_count,
        "customers": customers_count,
        "orders": orders_count,
        "sales": sales
    })


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():

    return jsonify({
        "status": "H&S Clothing backend is running"
    })


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found(error):

    return jsonify({
        "error": "Route not found"
    }), 404


@app.errorhandler(500)
def server_error(error):

    return jsonify({
        "error": "Internal server error"
    }), 500


# ============================================================
# INITIALIZE DATABASE
# ============================================================

init_database()


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get("PORT", 5000)
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
            )
