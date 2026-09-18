```python
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# --------------------------------------------------
# PRODUCTS
# --------------------------------------------------

products = [
    {
        "id": 1,
        "name": "Black Luxury Suit",
        "category": "Men",
        "type": "Formal",
        "price": 4999,
        "image": "https://images.unsplash.com/photo-1598808503746-f34c53b9323e?auto=format&fit=crop&w=800&q=85"
    },
    {
        "id": 2,
        "name": "Classic White Shirt",
        "category": "Men",
        "type": "Formal",
        "price": 1499,
        "image": "https://images.unsplash.com/photo-1603252110481-7ba873bf42ab?auto=format&fit=crop&w=800&q=85"
    },
    {
        "id": 3,
        "name": "Premium Black Dress",
        "category": "Women",
        "type": "Formal",
        "price": 2999,
        "image": "https://images.unsplash.com/photo-1539008835657-9e8e9680c956?auto=format&fit=crop&w=800&q=85"
    },
    {
        "id": 4,
        "name": "Luxury Blazer",
        "category": "Men",
        "type": "Formal",
        "price": 3499,
        "image": "https://images.unsplash.com/photo-1555069519-127aadedf1ee?auto=format&fit=crop&w=800&q=85"
    },
    {
        "id": 5,
        "name": "Urban Street Jacket",
        "category": "Men",
        "type": "Streetwear",
        "price": 2299,
        "image": "https://images.unsplash.com/photo-1551028719-00167b16eac5?auto=format&fit=crop&w=800&q=85"
    },
    {
        "id": 6,
        "name": "Elegant Evening Dress",
        "category": "Women",
        "type": "Formal",
        "price": 3299,
        "image": "https://images.unsplash.com/photo-1566174053879-31528523f8ae?auto=format&fit=crop&w=800&q=85"
    },
    {
        "id": 7,
        "name": "Premium Denim Jacket",
        "category": "Men",
        "type": "Streetwear",
        "price": 1999,
        "image": "https://images.unsplash.com/photo-1516826957135-700dedea698c?auto=format&fit=crop&w=800&q=85"
    },
    {
        "id": 8,
        "name": "Luxury Women's Blazer",
        "category": "Women",
        "type": "Formal",
        "price": 2799,
        "image": "https://images.unsplash.com/photo-1591369822096-ffd140ec948f?auto=format&fit=crop&w=800&q=85"
    }
]


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")


# --------------------------------------------------
# PRODUCTS API
# --------------------------------------------------

@app.route("/api/products", methods=["GET"])
def get_products():
    return jsonify(products)


# --------------------------------------------------
# SINGLE PRODUCT
# --------------------------------------------------

@app.route("/api/products/<int:product_id>", methods=["GET"])
def get_product(product_id):

    product = next(
        (p for p in products if p["id"] == product_id),
        None
    )

    if not product:
        return jsonify({
            "error": "Product not found"
        }), 404

    return jsonify(product)


# --------------------------------------------------
# REGISTER
# --------------------------------------------------

users = []


@app.route("/api/register", methods=["POST"])
def register():

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "No data received"
        }), 400

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({
            "success": False,
            "message": "Please fill all fields"
        }), 400

    existing_user = next(
        (user for user in users if user["email"] == email),
        None
    )

    if existing_user:
        return jsonify({
            "success": False,
            "message": "Email already registered"
        }), 409

    users.append({
        "name": name,
        "email": email,
        "password": password
    })

    return jsonify({
        "success": True,
        "message": "Registration successful"
    })


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "No data received"
        }), 400

    email = data.get("email")
    password = data.get("password")

    user = next(
        (
            user for user in users
            if user["email"] == email
            and user["password"] == password
        ),
        None
    )

    if not user:
        return jsonify({
            "success": False,
            "message": "Invalid email or password"
        }), 401

    return jsonify({
        "success": True,
        "message": "Login successful",
        "user": {
            "name": user["name"],
            "email": user["email"]
        }
    })


# --------------------------------------------------
# ORDERS
# --------------------------------------------------

orders = []


@app.route("/api/orders", methods=["POST"])
def create_order():

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "No order data received"
        }), 400

    order = {
        "id": len(orders) + 1,
        "customer": data.get("customer"),
        "items": data.get("items", []),
        "total": data.get("total", 0)
    }

    orders.append(order)

    return jsonify({
        "success": True,
        "message": "Order created successfully",
        "order": order
    }), 201


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.route("/health")
def health():
    return jsonify({
        "status": "H&S Clothing backend is running"
    })


# --------------------------------------------------
# RUN SERVER
# --------------------------------------------------

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
```
