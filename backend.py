from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# -----------------------------
# PRODUCTS
# -----------------------------

products = [
    {
        "id": 1,
        "name": "Classic Black Suit",
        "category": "Men",
        "type": "Formal",
        "price": 4999,
        "image": "https://images.unsplash.com/photo-1598808503746-f34c53b9323e?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": 2,
        "name": "Premium White Shirt",
        "category": "Men",
        "type": "Formal",
        "price": 1499,
        "image": "https://images.unsplash.com/photo-1603252110481-7ba873bf42ab?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": 3,
        "name": "Luxury Black Dress",
        "category": "Women",
        "type": "Formal",
        "price": 3999,
        "image": "https://images.unsplash.com/photo-1566174053879-31528523f8ae?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": 4,
        "name": "Streetwear Hoodie",
        "category": "Men",
        "type": "Streetwear",
        "price": 1999,
        "image": "https://images.unsplash.com/photo-1556821840-3a63f95609a7?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": 5,
        "name": "Women's Casual Outfit",
        "category": "Women",
        "type": "Casual",
        "price": 2499,
        "image": "https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": 6,
        "name": "Premium Blazer",
        "category": "Men",
        "type": "Formal",
        "price": 5499,
        "image": "https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": 7,
        "name": "Elegant Women's Dress",
        "category": "Women",
        "type": "Party",
        "price": 3499,
        "image": "https://images.unsplash.com/photo-1595777457583-95e059d581b8?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": 8,
        "name": "Urban Streetwear",
        "category": "Men",
        "type": "Streetwear",
        "price": 2299,
        "image": "https://images.unsplash.com/photo-1529139574466-a303027c1d8b?auto=format&fit=crop&w=800&q=80"
    }
]


# -----------------------------
# HOME PAGE
# -----------------------------

@app.route("/")
def home():
    return render_template("index.html")


# -----------------------------
# PRODUCTS API
# -----------------------------

@app.route("/api/products", methods=["GET"])
def get_products():
    return jsonify(products)


@app.route("/api/products/<int:product_id>", methods=["GET"])
def get_product(product_id):

    product = next(
        (p for p in products if p["id"] == product_id),
        None
    )

    if product is None:
        return jsonify({"error": "Product not found"}), 404

    return jsonify(product)


# -----------------------------
# USERS
# -----------------------------

users = []


@app.route("/api/register", methods=["POST"])
def register():

    data = request.get_json()

    if not data:
        return jsonify({"error": "No data received"}), 400

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({
            "error": "Name, email and password are required"
        }), 400

    for user in users:
        if user["email"] == email:
            return jsonify({
                "error": "Email already registered"
            }), 400

    users.append({
        "name": name,
        "email": email,
        "password": password
    })

    return jsonify({
        "message": "Registration successful"
    }), 201


@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json()

    if not data:
        return jsonify({"error": "No data received"}), 400

    email = data.get("email")
    password = data.get("password")

    for user in users:

        if (
            user["email"] == email
            and user["password"] == password
        ):
            return jsonify({
                "message": "Login successful",
                "user": {
                    "name": user["name"],
                    "email": user["email"]
                }
            })

    return jsonify({
        "error": "Invalid email or password"
    }), 401


# -----------------------------
# ORDERS
# -----------------------------

orders = []


@app.route("/api/orders", methods=["POST"])
def create_order():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "No order data received"
        }), 400

    order = {
        "id": len(orders) + 1,
        "data": data
    }

    orders.append(order)

    return jsonify({
        "message": "Order created successfully",
        "order": order
    }), 201


# -----------------------------
# HEALTH CHECK
# -----------------------------

@app.route("/health")
def health():

    return jsonify({
        "status": "H&S Clothing backend is running"
    })


# -----------------------------
# START SERVER
# -----------------------------

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
