from flask import Flask, request, jsonify
import sqlite3
import json
import os

DATABASE = 'users.db'

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

app = Flask(__name__)

def hash_password(password):
    return f"hashed_{password}"

def check_password(password, hashed_password):
    return f"hashed_{password}" == hashed_password

@app.route('/')
def home():
    return "User Management System"

@app.route('/users', methods=['GET'])
def get_all_users():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, name, email FROM users")
    users = cursor.fetchall()

    user_list = [dict(row) for row in users]

    return jsonify(user_list)

@app.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, name, email FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    if user:
        return jsonify(dict(user))
    else:
        return jsonify({"error": "User not found"}), 404

@app.route('/users', methods=['POST'])
def create_user():
    data = request.json
    if not data or 'name' not in data or 'email' not in data or 'password' not in data:
        return jsonify({"error": "Invalid input"}), 400

    hashed_pass = hash_password(data['password'])

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                       (data['name'], data['email'], hashed_pass))
        db.commit()
        return jsonify({"status": "success", "user_id": cursor.lastrowid}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already exists"}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/user/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.json
    if not data:
        return jsonify({"error": "Invalid data"}), 400

    db = get_db()
    cursor = db.cursor()
    updates = []
    params = []

    if 'name' in data:
        updates.append("name = ?")
        params.append(data['name'])
    if 'email' in data:
        updates.append("email = ?")
        params.append(data['email'])

    if not updates:
        return jsonify({"error": "No fields to update"}), 400

    params.append(user_id)
    query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"

    cursor.execute(query, tuple(params))
    db.commit()

    if cursor.rowcount == 0:
        return jsonify({"error": "User not found"}), 404
    else:
        return jsonify({"status": "User updated"}), 200

@app.route('/user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()

    if cursor.rowcount == 0:
        return jsonify({"error": "User not found"}), 404
    else:
        return jsonify({"status": "User deleted"}), 200

@app.route('/search', methods=['GET'])
def search_users():
    name = request.args.get('name')
    if not name:
        return jsonify({"error": "Please provide a name to search"}), 400

    db = get_db()
    cursor = db.cursor()
    search_term = f'%{name}%'
    cursor.execute("SELECT id, name, email FROM users WHERE name LIKE ?", (search_term,))
    users = cursor.fetchall()

    if users:
        user_list = [dict(row) for row in users]
        return jsonify(user_list)
    else:
        return jsonify({"message": "No users found"}), 404

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({"error": "Invalid input"}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, password FROM users WHERE email = ?", (data['email'],))
    user = cursor.fetchone()

    if user and check_password(data['password'], user['password']):
        return jsonify({"status": "success", "user_id": user['id']})
    else:
        return jsonify({"status": "failed", "message": "Invalid credentials"}), 401

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        print("Database not found. Please run init_db.py first.")
    else:
        app.run(host='0.0.0.0', port=5009, debug=True)