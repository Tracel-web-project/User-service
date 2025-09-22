import os
from flask import Flask, request, jsonify
import sqlite3
from flask_cors import CORS
from functools import wraps

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Set up folder and DB path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(BASE_DIR, 'data')
os.makedirs(data_dir, exist_ok=True)   # creates folder if missing
db_path = os.path.join(data_dir, 'users.db')

# Connect to DB
conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    role TEXT DEFAULT 'user'
)
''')
conn.commit()

# ===================== RBAC Decorator =====================
def rbac(allowed_roles):
    """Allow only users with roles in allowed_roles to access the endpoint"""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            data = request.json or {}
            email = data.get("email")
            if not email:
                return jsonify({"error": "Email required"}), 400

            cursor.execute("SELECT role FROM users WHERE email=?", (email,))
            user = cursor.fetchone()
            if not user:
                return jsonify({"error": "User not registered"}), 403

            role = user[0]
            if role not in allowed_roles:
                return jsonify({"error": f"Permission denied for role '{role}'"}), 403

            return f(*args, **kwargs)
        return wrapped
    return decorator

# ===================== Login / Registration =====================
@app.route('/api/user/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    cursor.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
    user = cursor.fetchone()

    if user:
        return jsonify({"message": "Logged in successfully", "name": user[1], "role": user[4]})
    else:
        # Auto-register new users with default role 'user'
        name = email.split('@')[0]  # default name
        role = "user"
        cursor.execute(
            "INSERT OR IGNORE INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
            (name, email, password, role)
        )
        conn.commit()
        return jsonify({"message": "Registered successfully", "name": name, "role": role})

# ===================== Example RBAC endpoints =====================
# AI task endpoint: accessible to both 'user' and 'admin'
@app.route('/api/ai/task', methods=['POST'])
@rbac(['user', 'admin'])
def ai_task():
    data = request.json
    return jsonify({"message": "AI task performed successfully"})

# Admin-only endpoint
@app.route('/api/admin/data', methods=['GET'])
@rbac(['admin'])
def admin_data():
    return jsonify({"message": "Admin-only data access"})

# Admin can promote a user
@app.route('/api/admin/promote', methods=['POST'])
@rbac(['admin'])
def promote_user():
    data = request.json
    target_email = data.get("target_email")
    if not target_email:
        return jsonify({"error": "target_email required"}), 400

    cursor.execute("UPDATE users SET role='admin' WHERE email=?", (target_email,))
    conn.commit()
    return jsonify({"message": f"{target_email} promoted to admin"})

# ==========================================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

