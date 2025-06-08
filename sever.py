from flask import Flask, request, jsonify
import sqlite3
import os
import hashlib
import traceback

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'users.db')

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
            background_color TEXT DEFAULT '#ffffff',
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
    """)

    # 기존 settings 테이블에 컬럼이 없을 경우 대비해서 background_color 추가
    try:
        cur.execute("ALTER TABLE settings ADD COLUMN background_color TEXT DEFAULT '#ffffff'")
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e):
            raise

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

# --- 루트 경로 (상태 확인용) ---
@app.route('/')
def index():
    return "API 서버가 정상 작동 중입니다."

# --- 로그인 API ---
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, password FROM users WHERE id=?", (data['username'],))
    user = cur.fetchone()
    conn.close()

    # 서버에서 평문 비밀번호 해시 처리 후 비교
    if user and user["password"] == hash_password(data["password"]):
        return jsonify({"status": "success", "us
