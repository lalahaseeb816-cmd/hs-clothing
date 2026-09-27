import os
import sqlite3
from datetime import datetime
from functools import wraps

from flask import (
    Flask,
    jsonify,
    request,
    session,
    send_from_directory,
    redirect,
    url_for,
)
from flask_cors import CORS
from werkzeug.utils import secure_filename


# ============================================================
# APP CONFIGURATION
# ============================================================

app = Flask(__name__)

CORS(
    app,
    supports_credentials=True,
)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "hs-clothing-secret-key-change-this"
)

app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Render Persistent Disk:
# Set DATABASE_PATH in Render Environment Variables if you have
# a persistent disk mounted.
DATABASE_PATH = os.environ.get(
    "DATABASE_PATH",
    os.path.join(BASE_DIR, "hands_clothing.db")
)

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "webp",
    "gif",
}


# ============================================================
# ADMIN CONFIGURATION
# ============================================================

ADMIN_USERNAME = os.environ.get(
    "ADMIN_USERNAME",
    "admin"
)

ADMIN_PASSWORD = os.environ.get(
    "ADMIN_PASSWORD",
    "admin123"
)


# ============================================================
# DATABASE
# ============================================================

def get_db():
    conn = sqlite3.connect(
        DATABASE_PATH,
        timeout=30
    )

    conn.row_factory = sqlite3.Row

    return conn


def init_database():
    conn = get_db()
    cursor = conn.cursor()

    # Products
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL DEFAULT 0,
            category TEXT DEFAULT '',
            description TEXT DEFAULT '',
            image TEXT DEFAULT '',
            celebrity TEXT DEFAULT '',
            stock INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Orders
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT DEFAULT '',
            email TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            address TEXT DEFAULT '',
            items TEXT DEFAULT '',
            total REAL DEFAULT 0,
            status TEXT DEFAULT 'Pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Customers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT DEFAULT '',
            email TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()

    # --------------------------------------------------------
    # IMPORTANT:
    # Do NOT automatically insert the seed products every time.
    #
    # This prevents deleted products from coming back after
    # restarting the Render service.
    # --------------------------------------------------------

    cursor.execute("SELECT COUNT(*) FROM products")
    product_count = cursor.fetchone()[0]

    if product_count == 0:
        seed_products = [
            (
                "Black Luxury Suit",
                7999,
                "Formal",
                "Premium black luxury suit for a sophisticated look.",
                "",
                "",
                10,
            ),
            (
                "Classic White Shirt",
                2499,
                "Men",
                "Clean and elegant classic white shirt.",
                "",
                "",
                20,
            ),
            (
                "Premium Black Dress",
                5999,
                "Women",
                "Elegant premium black dress for special occasions.",
                "",
                "",
                10,
            ),
            (
                "Luxury Blazer",
                6499,
                "Formal",
                "Premium tailored blazer with a luxury finish.",
                "",
                "",
                10,
            ),
            (
                "Urban Street Jacket",
                4499,
                "Streetwear",
                "Modern streetwear jacket with a premium design.",
                "",
                "",
                15,
            ),
            (
                "Elegant Evening Dress",
                6999,
                "Women",
                "Elegant evening dress for parties and events.",
                "",
                "",
                10,
            ),
            (
                "Premium Denim Jacket",
                3999,
                "Streetwear",
                "Premium denim jacket for everyday style.",
                "",
                "",
                15,
            ),
            (
                "Luxury Women's Blazer",
                5499,
                "Women",
                "Elegant women's blazer with a premium cut.",
                "",
                "",
                10,
            ),
        ]

        cursor.executemany("""
            INSERT INTO products
            (
                name,
                price,
                category,
                description,
                image,
                celebrity,
                stock
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, seed_products)

        conn.commit()

    conn.close()


# ============================================================
# HELPERS
# ============================================================

def allowed_file(filename):
    if not filename:
        return False

    if "." not in filename:
        return False

    extension = filename.rsplit(".", 1)[1].lower()

    return extension in ALLOWED_EXTENSIONS


def product_to_dict(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "price": row["price"],
        "category": row["category"],
        "description": row["description"],
        "image": row["image"],
        "celebrity": row["celebrity"],
        "stock": row["stock"],
        "created_at": row["created_at"],
    }


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
# HOME
# ============================================================

@app.route("/")
def home():
    return """
    <h1>H&S Clothing Backend</h1>
    <p>Backend is running successfully.</p>
    <p>API: /api/products</p>
    <p>Admin: /admin</p>
    """


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():
    return jsonify({
        "success": True,
        "message": "H&S Clothing backend is running"
    })


# ============================================================
# PRODUCTS - PUBLIC
# ============================================================

@app.route("/api/products", methods=["GET"])
def get_products():

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM products
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    products = [
        product_to_dict(row)
        for row in rows
    ]

    return jsonify({
        "success": True,
        "count": len(products),
        "products": products
    })


# ============================================================
# SINGLE PRODUCT
# ============================================================

@app.route("/api/products/<int:product_id>", methods=["GET"])
def get_product(product_id):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,)
    )

    row = cursor.fetchone()

    conn.close()

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
# ADMIN LOGIN
# ============================================================

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "GET":
        return """
        <h2>H&S Clothing Admin Login</h2>

        <form method="POST">
            <input
                type="text"
                name="username"
                placeholder="Username"
                required
            >
            <br><br>

            <input
                type="password"
                name="password"
                placeholder="Password"
                required
            >
            <br><br>

            <button type="submit">
                Login
            </button>
        </form>
        """

    data = request.get_json(silent=True)

    if data:
        username = str(
            data.get("username", "")
        ).strip()

        password = str(
            data.get("password", "")
        )
    else:
        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

    if (
        username == ADMIN_USERNAME
        and password == ADMIN_PASSWORD
    ):
        session["admin_logged_in"] = True
        session.permanent = True

        return jsonify({
            "success": True,
            "message": "Login successful"
        })

    return jsonify({
        "success": False,
        "message": "Invalid username or password"
    }), 401


# ============================================================
# ADMIN LOGOUT
# ============================================================

@app.route("/admin-logout", methods=["GET", "POST"])
def admin_logout():

    session.clear()

    return jsonify({
        "success": True,
        "message": "Logged out successfully"
    })


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route("/admin")
def admin_dashboard():

    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    return """
    <h1>H&S Clothing Admin Dashboard</h1>
    <p>Admin login successful.</p>
    <p>Use the admin API from your frontend dashboard.</p>
    """


# ============================================================
# CREATE PRODUCT
# ============================================================

@app.route("/api/admin/products", methods=["POST"])
@admin_required
def create_product():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "success": False,
            "message": "JSON data required"
        }), 400

    name = str(
        data.get("name", "")
    ).strip()

    if not name:
        return jsonify({
            "success": False,
            "message": "Product name is required"
        }), 400

    try:
        price = float(
            data.get("price", 0)
        )
    except (TypeError, ValueError):
        price = 0

    try:
        stock = int(
            data.get("stock", 0)
        )
    except (TypeError, ValueError):
        stock = 0

    category = str(
        data.get("category", "")
    ).strip()

    description = str(
        data.get("description", "")
    ).strip()

    image = str(
        data.get("image", "")
    ).strip()

    celebrity = str(
        data.get("celebrity", "")
    ).strip()

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO products
        (
            name,
            price,
            category,
            description,
            image,
            celebrity,
            stock
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        name,
        price,
        category,
        description,
        image,
        celebrity,
        stock
    ))

    product_id = cursor.lastrowid

    conn.commit()

    conn.close()

    return jsonify({
        "success": True,
        "message": "Product created successfully",
        "product_id": product_id
    }), 201


# ============================================================
# UPDATE PRODUCT
# ============================================================

@app.route("/api/admin/products/<int:product_id>", methods=["PUT", "PATCH"])
@admin_required
def update_product(product_id):

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "success": False,
            "message": "JSON data required"
        }), 400

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,)
    )

    existing = cursor.fetchone()

    if not existing:
        conn.close()

        return jsonify({
            "success": False,
            "message": "Product not found"
        }), 404

    name = str(
        data.get("name", existing["name"])
    ).strip()

    try:
        price = float(
            data.get("price", existing["price"])
        )
    except (TypeError, ValueError):
        price = existing["price"]

    category = str(
        data.get(
            "category",
            existing["category"]
        )
    ).strip()

    description = str(
        data.get(
            "description",
            existing["description"]
        )
    ).strip()

    image = str(
        data.get(
            "image",
            existing["image"]
        )
    ).strip()

    celebrity = str(
        data.get(
            "celebrity",
            existing["celebrity"]
        )
    ).strip()

    try:
        stock = int(
            data.get(
                "stock",
                existing["stock"]
            )
        )
    except (TypeError, ValueError):
        stock = existing["stock"]

    cursor.execute("""
        UPDATE products
        SET
            name = ?,
            price = ?,
            category = ?,
            description = ?,
            image = ?,
            celebrity = ?,
            stock = ?
        WHERE id = ?
    """, (
        name,
        price,
        category,
        description,
        image,
        celebrity,
        stock,
        product_id
    ))

    conn.commit()

    conn.close()

    return jsonify({
        "success": True,
        "message": "Product updated successfully"
    })


# ============================================================
# DELETE PRODUCT
# ============================================================

@app.route("/api/admin/products/<int:product_id>", methods=["DELETE"])
@admin_required
def delete_product(product_id):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(
        "SELECT image FROM products WHERE id = ?",
        (product_id,)
    )

    product = cursor.fetchone()

    if not product:
        conn.close()

        return jsonify({
            "success": False,
            "message": "Product not found"
        }), 404

    cursor.execute(
        "DELETE FROM products WHERE id = ?",
        (product_id,)
    )

    conn.commit()

    conn.close()

    return jsonify({
        "success": True,
        "message": "Product deleted successfully"
    })


# ============================================================
# IMAGE UPLOAD
# ============================================================

@app.route("/api/upload-image", methods=["POST"])
@admin_required
def upload_image():

    if "image" not in request.files:
        return jsonify({
            "success": False,
            "message": "No image file provided"
        }), 400

    file = request.files["image"]

    if not file or not file.filename:
        return jsonify({
            "success": False,
            "message": "No image selected"
        }), 400

    if not allowed_file(file.filename):
        return jsonify({
            "success": False,
            "message": "Unsupported image format"
        }), 400

    filename = secure_filename(
        file.filename
    )

    # Add timestamp to prevent filename collisions
    timestamp = datetime.now().strftime(
        "%Y%m%d%H%M%S%f"
    )

    filename = f"{timestamp}_{filename}"

    filepath = os.path.join(
        UPLOAD_FOLDER,
        filename
    )

    file.save(filepath)

    image_url = (
        request.host_url.rstrip("/")
        + "/uploads/"
        + filename
    )

    return jsonify({
        "success": True,
        "message": "Image uploaded successfully",
        "filename": filename,
        "url": image_url
    })


# ============================================================
# SERVE UPLOADED IMAGES
# ============================================================

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):

    return send_from_directory(
        UPLOAD_FOLDER,
        filename
    )


# ============================================================
# CREATE ORDER
# ============================================================

@app.route("/api/orders", methods=["POST"])
def create_order():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "success": False,
            "message": "JSON data required"
        }), 400

    customer_name = str(
        data.get("customer_name", "")
    ).strip()

    email = str(
        data.get("email", "")
    ).strip()

    phone = str(
        data.get("phone", "")
    ).strip()

    address = str(
        data.get("address", "")
    ).strip()

    items = data.get(
        "items",
        []
    )

    try:
        total = float(
            data.get("total", 0)
        )
    except (TypeError, ValueError):
        total = 0

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO orders
        (
            customer_name,
            email,
            phone,
            address,
            items,
            total,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        customer_name,
        email,
        phone,
        address,
        str(items),
        total,
        "Pending"
    ))

    order_id = cursor.lastrowid

    # Save customer if email/phone exists
    if email or phone:

        cursor.execute("""
            SELECT id
            FROM customers
            WHERE
                (email != '' AND email = ?)
                OR
                (phone != '' AND phone = ?)
            LIMIT 1
        """, (
            email,
            phone
        ))

        customer = cursor.fetchone()

        if customer:
            cursor.execute("""
                UPDATE customers
                SET
                    name = ?,
                    email = ?,
                    phone = ?
                WHERE id = ?
            """, (
                customer_name,
                email,
                phone,
                customer["id"]
            ))
        else:
            cursor.execute("""
                INSERT INTO customers
                (
                    name,
                    email,
                    phone
                )
                VALUES (?, ?, ?)
            """, (
                customer_name,
                email,
                phone
            ))

    conn.commit()

    conn.close()

    return jsonify({
        "success": True,
        "message": "Order placed successfully",
        "order_id": order_id
    }), 201


# ============================================================
# ADMIN ORDERS
# ============================================================

@app.route("/api/admin/orders", methods=["GET"])
@admin_required
def get_orders():

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM orders
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    orders = []

    for row in rows:

        orders.append({
            "id": row["id"],
            "customer_name": row["customer_name"],
            "email": row["email"],
            "phone": row["phone"],
            "address": row["address"],
            "items": row["items"],
            "total": row["total"],
            "status": row["status"],
            "created_at": row["created_at"],
        })

    return jsonify({
        "success": True,
        "count": len(orders),
        "orders": orders
    })


# ============================================================
# UPDATE ORDER STATUS
# ============================================================

@app.route(
    "/api/admin/orders/<int:order_id>",
    methods=["PUT", "PATCH"]
)
@admin_required
def update_order(order_id):

    data = request.get_json(silent=True) or {}

    status = str(
        data.get(
            "status",
            "Pending"
        )
    ).strip()

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM orders WHERE id = ?",
        (order_id,)
    )

    order = cursor.fetchone()

    if not order:
        conn.close()

        return jsonify({
            "success": False,
            "message": "Order not found"
        }), 404

    cursor.execute("""
        UPDATE orders
        SET status = ?
        WHERE id = ?
    """, (
        status,
        order_id
    ))

    conn.commit()

    conn.close()

    return jsonify({
        "success": True,
        "message": "Order status updated"
    })


# ============================================================
# ADMIN CUSTOMERS
# ============================================================

@app.route("/api/admin/customers", methods=["GET"])
@admin_required
def get_customers():

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM customers
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    customers = []

    for row in rows:

        customers.append({
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
            "phone": row["phone"],
            "created_at": row["created_at"],
        })

    return jsonify({
        "success": True,
        "count": len(customers),
        "customers": customers
    })


# ============================================================
# ADMIN STATISTICS
# ============================================================

@app.route("/api/admin/stats", methods=["GET"])
@admin_required
def admin_stats():

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM products"
    )
    products = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM orders"
    )
    orders = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM customers"
    )
    customers = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(total), 0)
        FROM orders
    """)

    revenue = cursor.fetchone()[0]

    conn.close()

    return jsonify({
        "success": True,
        "stats": {
            "products": products,
            "orders": orders,
            "customers": customers,
            "revenue": revenue
        }
    })


# ============================================================
# STARTUP
# ============================================================

init_database()


# ============================================================
# LOCAL DEVELOPMENT
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
        )
 
