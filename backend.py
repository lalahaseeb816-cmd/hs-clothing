import os
import sqlite3
import uuid
from functools import wraps

from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    session,
    redirect,
    send_from_directory
)
from flask_cors import CORS
from werkzeug.utils import secure_filename


# ============================================================
# APP CONFIG
# ============================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "change-this-secret-key"
)

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = (
    os.environ.get("SESSION_COOKIE_SECURE", "true").lower() == "true"
)

# Maximum upload size: 8 MB
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

CORS(app, supports_credentials=True)


# ============================================================
# ADMIN LOGIN
# ============================================================

ADMIN_USERNAME = os.environ.get(
    "ADMIN_USERNAME",
    "admin"
)

ADMIN_PASSWORD = os.environ.get(
    "ADMIN_PASSWORD",
    "change-this-password"
)


# ============================================================
# DATABASE
# ============================================================

DATABASE = os.environ.get(
    "DATABASE_PATH",
    "hands_clothing.db"
)


def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


def column_exists(db, table, column):
    columns = db.execute(
        f"PRAGMA table_info({table})"
    ).fetchall()

    return any(row["name"] == column for row in columns)


# ============================================================
# IMAGE UPLOAD CONFIGURATION
# ============================================================

UPLOAD_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "uploads"
)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "webp",
    "gif"
}


def allowed_file(filename):
    if not filename or "." not in filename:
        return False

    extension = filename.rsplit(".", 1)[1].lower()

    return extension in ALLOWED_EXTENSIONS


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_database():

    db = get_db()

    # USERS
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # PRODUCTS
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

    # ORDERS
    db.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            order_data TEXT NOT NULL,
            total REAL DEFAULT 0,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Add extra product fields
    if not column_exists(db, "products", "celebrity"):
        db.execute(
            "ALTER TABLE products ADD COLUMN celebrity TEXT DEFAULT ''"
        )

    if not column_exists(db, "products", "stock"):
        db.execute(
            "ALTER TABLE products ADD COLUMN stock INTEGER DEFAULT 10"
        )

    db.commit()

    # Seed products only when empty
    count = db.execute(
        "SELECT COUNT(*) FROM products"
    ).fetchone()[0]

    if count == 0:

        products = [

            (
                "Black Luxury Suit",
                "Men",
                "Formal",
                4999,
                "https://images.unsplash.com/photo-1598808503746-f34c53b9323e?auto=format&fit=crop&w=900&q=80",
                "Bollywood Inspired",
                10
            ),

            (
                "Classic White Shirt",
                "Men",
                "Formal",
                1499,
                "https://images.unsplash.com/photo-1603252110481-7ba873bf42ab?auto=format&fit=crop&w=900&q=80",
                "Classic Celebrity Style",
                15
            ),

            (
                "Premium Black Dress",
                "Women",
                "Formal",
                2999,
                "https://images.unsplash.com/photo-1566174053879-31528523f8ae?auto=format&fit=crop&w=900&q=80",
                "Bollywood Inspired",
                8
            ),

            (
                "Luxury Blazer",
                "Men",
                "Formal",
                3499,
                "https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&w=900&q=80",
                "Hollywood Inspired",
                12
            ),

            (
                "Urban Street Jacket",
                "Men",
                "Streetwear",
                2299,
                "https://images.unsplash.com/photo-1551488831-00ddcb6c6bd3?auto=format&fit=crop&w=900&q=80",
                "Celebrity Street Style",
                10
            ),

            (
                "Elegant Evening Dress",
                "Women",
                "Formal",
                3299,
                "https://images.unsplash.com/photo-1566174053879-31528523f8ae?auto=format&fit=crop&w=900&q=80",
                "Red Carpet Inspired",
                7
            ),

            (
                "Premium Denim Jacket",
                "Men",
                "Streetwear",
                1999,
                "https://images.unsplash.com/photo-1543076447-215ad9ba6923?auto=format&fit=crop&w=900&q=80",
                "Hollywood Inspired",
                14
            ),

            (
                "Luxury Women's Blazer",
                "Women",
                "Formal",
                2799,
                "https://images.unsplash.com/photo-1591369822096-ffd140ec948f?auto=format&fit=crop&w=900&q=80",
                "Bollywood Inspired",
                9
            )

        ]

        db.executemany("""
            INSERT INTO products
            (name, category, type, price, image, celebrity, stock)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, products)

        db.commit()

    db.close()


# ============================================================
# AUTHENTICATION
# ============================================================

def admin_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if not session.get("admin_logged_in"):

            return jsonify({
                "success": False,
                "message": "Admin login required"
            }), 401

        return function(*args, **kwargs)

    return wrapper


# ============================================================
# PAGE ROUTES
# ============================================================

@app.route("/")
def home():

    return render_template("index.html")


@app.route("/admin-login")
def admin_login_page():

    if session.get("admin_logged_in"):
        return redirect("/admin")

    return render_template("admin-login.html")


@app.route("/admin")
def admin_page():

    if not session.get("admin_logged_in"):
        return redirect("/admin-login")

    return render_template("admin.html")


# ============================================================
# UPLOADED IMAGE ROUTE
# ============================================================

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):

    return send_from_directory(
        UPLOAD_FOLDER,
        filename
    )


# ============================================================
# ADMIN LOGIN API
# ============================================================

@app.route("/api/admin/login", methods=["POST"])
def admin_login():

    data = request.get_json(silent=True) or {}

    username = str(
        data.get("username", "")
    ).strip()

    password = str(
        data.get("password", "")
    )

    if (
        username == ADMIN_USERNAME
        and password == ADMIN_PASSWORD
    ):

        session.clear()

        session["admin_logged_in"] = True
        session["admin_username"] = username

        return jsonify({
            "success": True,
            "message": "Login successful"
        })

    return jsonify({
        "success": False,
        "message": "Invalid username or password"
    }), 401


@app.route("/api/admin/me", methods=["GET"])
def admin_me():

    if session.get("admin_logged_in"):

        return jsonify({
            "success": True,
            "logged_in": True,
            "username": session.get("admin_username")
        })

    return jsonify({
        "success": True,
        "logged_in": False
    })


@app.route("/api/admin/logout", methods=["POST"])
def admin_logout():

    session.clear()

    return jsonify({
        "success": True,
        "message": "Logged out"
    })


# ============================================================
# PRODUCT HELPERS
# ============================================================

def product_to_dict(row):

    return {
        "id": row["id"],
        "name": row["name"],
        "category": row["category"],
        "type": row["type"] or "",
        "price": float(row["price"]),
        "image": row["image"] or "",
        "celebrity": (
            row["celebrity"]
            if "celebrity" in row.keys()
            else ""
        ),
        "stock": (
            int(row["stock"])
            if "stock" in row.keys()
            else 0
        ),
        "created_at": row["created_at"]
    }


# ============================================================
# PUBLIC PRODUCTS API
# ============================================================

@app.route("/api/products", methods=["GET"])
def get_products():

    db = get_db()

    rows = db.execute("""
        SELECT *
        FROM products
        ORDER BY id DESC
    """).fetchall()

    db.close()

    return jsonify({
        "success": True,
        "products": [
            product_to_dict(row)
            for row in rows
        ]
    })


@app.route("/api/products/<int:product_id>", methods=["GET"])
def get_product(product_id):

    db = get_db()

    row = db.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()

    db.close()

    if not row:

        return jsonify({
            "success": False,
            "message": "Product not found"
        }), 404

    return jsonify({
        "success": True,
        "product": product_to_dict(row)
    })


# ============================================================
# IMAGE UPLOAD API
# ============================================================

@app.route("/api/upload-image", methods=["POST"])
@admin_required
def upload_image():

    if "image" not in request.files:

        return jsonify({
            "success": False,
            "message": "No image file selected"
        }), 400

    file = request.files["image"]

    if not file or file.filename == "":

        return jsonify({
            "success": False,
            "message": "Please select an image"
        }), 400

    if not allowed_file(file.filename):

        return jsonify({
            "success": False,
            "message": (
                "Invalid image format. "
                "Use JPG, JPEG, PNG, WEBP or GIF."
            )
        }), 400

    original_name = secure_filename(
        file.filename
    )

    extension = original_name.rsplit(
        ".",
        1
    )[1].lower()

    unique_name = (
        uuid.uuid4().hex
        + "."
        + extension
    )

    save_path = os.path.join(
        UPLOAD_FOLDER,
        unique_name
    )

    file.save(save_path)

    image_url = "/uploads/" + unique_name

    return jsonify({
        "success": True,
        "message": "Image uploaded successfully",
        "image": image_url
    })


# ============================================================
# ADMIN PRODUCT CREATE
# ============================================================

@app.route("/api/products", methods=["POST"])
@admin_required
def create_product():

    data = request.get_json(silent=True) or {}

    name = str(
        data.get("name", "")
    ).strip()

    category = str(
        data.get("category", "Men")
    ).strip()

    product_type = str(
        data.get("type", "General")
    ).strip()

    image = str(
        data.get("image", "")
    ).strip()

    celebrity = str(
        data.get("celebrity", "")
    ).strip()

    try:

        price = float(
            data.get("price", 0)
        )

        stock = int(
            data.get("stock", 10)
        )

    except (TypeError, ValueError):

        return jsonify({
            "success": False,
            "message": "Price and stock must be valid numbers"
        }), 400

    if not name:

        return jsonify({
            "success": False,
            "message": "Product name is required"
        }), 400

    if price < 0:

        return jsonify({
            "success": False,
            "message": "Price cannot be negative"
        }), 400

    if stock < 0:

        return jsonify({
            "success": False,
            "message": "Stock cannot be negative"
        }), 400

    db = get_db()

    cursor = db.execute("""
        INSERT INTO products
        (name, category, type, price, image, celebrity, stock)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        name,
        category,
        product_type,
        price,
        image,
        celebrity,
        stock
    ))

    db.commit()

    product_id = cursor.lastrowid

    row = db.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()

    db.close()

    return jsonify({
        "success": True,
        "message": "Product added successfully",
        "product": product_to_dict(row)
    }), 201


# ============================================================
# ADMIN PRODUCT UPDATE
# ============================================================

@app.route("/api/products/<int:product_id>", methods=["PUT"])
@admin_required
def update_product(product_id):

    data = request.get_json(silent=True) or {}

    name = str(
        data.get("name", "")
    ).strip()

    category = str(
        data.get("category", "Men")
    ).strip()

    product_type = str(
        data.get("type", "General")
    ).strip()

    image = str(
        data.get("image", "")
    ).strip()

    celebrity = str(
        data.get("celebrity", "")
    ).strip()

    try:

        price = float(
            data.get("price", 0)
        )

        stock = int(
            data.get("stock", 10)
        )

    except (TypeError, ValueError):

        return jsonify({
            "success": False,
            "message": "Price and stock must be valid numbers"
        }), 400

    if not name:

        return jsonify({
            "success": False,
            "message": "Product name is required"
        }), 400

    if price < 0 or stock < 0:

        return jsonify({
            "success": False,
            "message": "Price and stock cannot be negative"
        }), 400

    db = get_db()

    existing = db.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()

    if not existing:

        db.close()

        return jsonify({
            "success": False,
            "message": "Product not found"
        }), 404

    db.execute("""
        UPDATE products
        SET name = ?,
            category = ?,
            type = ?,
            price = ?,
            image = ?,
            celebrity = ?,
            stock = ?
        WHERE id = ?
    """, (
        name,
        category,
        product_type,
        price,
        image,
        celebrity,
        stock,
        product_id
    ))

    db.commit()

    row = db.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()

    db.close()

    return jsonify({
        "success": True,
        "message": "Product updated successfully",
        "product": product_to_dict(row)
    })


# ============================================================
# ADMIN PRODUCT DELETE
# ============================================================

@app.route("/api/products/<int:product_id>", methods=["DELETE"])
@admin_required
def delete_product(product_id):

    db = get_db()

    existing = db.execute(
        "SELECT image FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()

    if not existing:

        db.close()

        return jsonify({
            "success": False,
            "message": "Product not found"
        }), 404

    image = existing["image"]

    db.execute(
        "DELETE FROM products WHERE id = ?",
        (product_id,)
    )

    db.commit()

    db.close()

    # Delete uploaded image if it belongs to our uploads folder
    if image and image.startswith("/uploads/"):

        filename = image.replace(
            "/uploads/",
            "",
            1
        )

        filename = os.path.basename(filename)

        image_path = os.path.join(
            UPLOAD_FOLDER,
            filename
        )

        if os.path.isfile(image_path):

            try:
                os.remove(image_path)
            except OSError:
                pass

    return jsonify({
        "success": True,
        "message": "Product deleted successfully"
    })


# ============================================================
# ADMIN DASHBOARD STATS
# ============================================================

@app.route("/api/admin/stats", methods=["GET"])
@admin_required
def admin_stats():

    db = get_db()

    product_count = db.execute(
        "SELECT COUNT(*) FROM products"
    ).fetchone()[0]

    order_count = db.execute(
        "SELECT COUNT(*) FROM orders"
    ).fetchone()[0]

    customer_count = db.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone()[0]

    sales = db.execute(
        "SELECT COALESCE(SUM(total), 0) FROM orders"
    ).fetchone()[0]

    db.close()

    return jsonify({
        "success": True,
        "stats": {
            "products": product_count,
            "orders": order_count,
            "customers": customer_count,
            "sales": float(sales or 0)
        }
    })


# ============================================================
# ADMIN ORDERS
# ============================================================

@app.route("/api/admin/orders", methods=["GET"])
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
            users.name AS customer_name,
            users.email AS customer_email
        FROM orders
        LEFT JOIN users
            ON orders.user_id = users.id
        ORDER BY orders.id DESC
    """).fetchall()

    db.close()

    orders = []

    for row in rows:

        orders.append({
            "id": row["id"],
            "customer_name": (
                row["customer_name"]
                or "Guest"
            ),
            "customer_email": (
                row["customer_email"]
                or "N/A"
            ),
            "total": float(
                row["total"] or 0
            ),
            "status": (
                row["status"]
                or "Pending"
            ),
            "created_at": row["created_at"],
            "order_data": row["order_data"]
        })

    return jsonify({
        "success": True,
        "orders": orders
    })


# ============================================================
# ADMIN CUSTOMERS
# ============================================================

@app.route("/api/admin/customers", methods=["GET"])
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

    customers = []

    for row in rows:

        customers.append({
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
            "created_at": row["created_at"]
        })

    return jsonify({
        "success": True,
        "customers": customers
    })


# ============================================================
# CUSTOMER REGISTER
# ============================================================

@app.route("/api/register", methods=["POST"])
def register():

    data = request.get_json(silent=True) or {}

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
            "success": False,
            "message": (
                "Name, email and password are required"
            )
        }), 400

    db = get_db()

    existing = db.execute(
        "SELECT id FROM users WHERE email = ?",
        (email,)
    ).fetchone()

    if existing:

        db.close()

        return jsonify({
            "success": False,
            "message": "Email already registered"
        }), 409

    db.execute("""
        INSERT INTO users
        (name, email, password)
        VALUES (?, ?, ?)
    """, (
        name,
        email,
        password
    ))

    db.commit()

    db.close()

    return jsonify({
        "success": True,
        "message": "Account created successfully"
    }), 201


# ============================================================
# CREATE ORDER
# ============================================================

@app.route("/api/orders", methods=["POST"])
def create_order():

    data = request.get_json(silent=True) or {}

    order_data = data.get(
        "order_data",
        data.get("items", [])
    )

    try:

        total = float(
            data.get("total", 0)
        )

    except (TypeError, ValueError):

        total = 0

    user_id = data.get("user_id")

    db = get_db()

    cursor = db.execute("""
        INSERT INTO orders
        (user_id, order_data, total, status)
        VALUES (?, ?, ?, ?)
    """, (
        user_id,
        str(order_data),
        total,
        "Pending"
    ))

    db.commit()

    order_id = cursor.lastrowid

    db.close()

    return jsonify({
        "success": True,
        "message": "Order created successfully",
        "order_id": order_id
    }), 201


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():

    return jsonify({
        "success": True,
        "status": "H&S Clothing Backend is Running!"
    })


# ============================================================
# START DATABASE
# ============================================================

init_database()


# ============================================================
# LOCAL DEVELOPMENT
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),
        debug=False
    )
