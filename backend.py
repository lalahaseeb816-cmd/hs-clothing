import os
import sqlite3
import uuid
import json
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
# APP
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

app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

CORS(app, supports_credentials=True)


# ============================================================
# ADMIN
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
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATABASE = os.environ.get(
    "DATABASE_PATH",
    os.path.join(BASE_DIR, "hands_clothing.db")
)

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads"
)

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# ============================================================
# DATABASE
# ============================================================

def get_db():
    db = sqlite3.connect(
        DATABASE,
        timeout=30
    )

    db.row_factory = sqlite3.Row

    return db


def column_exists(db, table, column):
    columns = db.execute(
        f"PRAGMA table_info({table})"
    ).fetchall()

    return any(
        row["name"] == column
        for row in columns
    )


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

    # EXTRA PRODUCT COLUMNS
    if not column_exists(db, "products", "celebrity"):
        db.execute("""
            ALTER TABLE products
            ADD COLUMN celebrity TEXT DEFAULT ''
        """)

    if not column_exists(db, "products", "stock"):
        db.execute("""
            ALTER TABLE products
            ADD COLUMN stock INTEGER DEFAULT 10
        """)

    db.commit()

    # --------------------------------------------------------
    # SEED ONLY WHEN EMPTY
    # --------------------------------------------------------

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
                "
