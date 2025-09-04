import os
from flask import Flask, request, jsonify
import sqlite3
from flask_cors import CORS
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
    password TEXT
)
''')
conn.commit()

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    cursor.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
    user = cursor.fetchone()

    if user:
        return jsonify({"message": "Logged in successfully", "name": user[1]})
    else:
        # Register automatically if user doesn't exist
        name = email.split('@')[0]  # simple default name
        cursor.execute("INSERT OR IGNORE INTO users (name, email, password) VALUES (?, ?, ?)",
                       (name, email, password))
        conn.commit()
        return jsonify({"message": "Registered successfully", "name": name})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
