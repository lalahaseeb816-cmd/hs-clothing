import os
import sqlite3
from functools import wraps

from flask import Flask, render_template, jsonify, request, session, redirect
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
# ADMIN CREDENTIALS
# ============================================================

ADMIN_USERNAME = os.environ.get(
    "ADMIN_USERNAME",
    "lalahaseeb@816gmail.com"
)

ADMIN_PASSWORD = os.environ.get(
    "ADMIN_PASSWORD",
    "Haseeb12000"
)


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
            FOREIGN KEY (user_id) REFERENCES users(id)
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
                "https://images.unsplash
