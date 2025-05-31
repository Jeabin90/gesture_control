from flask import Flask, request, jsonify
import sqlite3
import os
import hashlib

app = Flask(__name__)
DB_PATH = 'users.db'

# --- 비밀번호 해시 처리 ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- DB 자동 초기화 ---
def init_db():
    db_exists = os.path.exists(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # users 테이블 생성
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT,
            phone TEXT,
            email TEXT,
            password TEXT
        );
    """)

    # settings 테이블 생성
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            user_id TEXT PRIMARY KEY,
            vgesture_command TEXT,
            sensitivity INTEGER DEFAULT 20,
            dark_mode BOOLEAN DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
    """)

    conn.commit()
    conn.close()
    if not db_exists:
        print("✅ Database created and initialized.")
    else:
        print("ℹ️ Database already exists, initialization ensured.")

# --- DB 연결 함수 ---
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- 로그인 API ---
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, password FROM users WHERE id=?", (data['username'],))
    user = cur.fetchone()
    if user and user["password"] == hash_password(data["password"]):
        return jsonify({"status": "success", "user_id": user["id"]})
    return jsonify({"status": "fail"}), 401

# --- 회원가입 API ---
import traceback

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE id=?", (data['id'],))
        if cur.fetchone():
            return jsonify({"status": "fail", "message": "이미 존재하는 ID입니다."}), 400
        cur.execute("""
            INSERT INTO users (id, name, phone, email, password)
            VALUES (?, ?, ?, ?, ?)
        """, (data['id'], data['name'], data['phone'], data['email'], hash_password(data['password'])))
        conn.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        print(traceback.format_exc())  # 에러 자세히 출력
        return jsonify({"status": "fail", "message": str(e)}), 500

# --- 서버 시작 ---
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=8080, debug=True)
