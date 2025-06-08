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
        return jsonify({"status": "success", "user_id": user["id"]})
    return jsonify({"status": "fail"}), 401

# --- 회원가입 API ---
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT id FROM users WHERE id=?", (data['id'],))
        if cur.fetchone():
            return jsonify({"status": "fail", "message": "이미 존재하는 ID입니다."}), 400

        # 비밀번호 해시 처리 후 저장
        cur.execute("""
            INSERT INTO users (id, name, phone, email, password)
            VALUES (?, ?, ?, ?, ?)
        """, (
            data['id'],
            data['name'],
            data['phone'],
            data['email'],
            hash_password(data['password'])
        ))

        # 기본 설정 저장
        cur.execute("""
            INSERT INTO settings (user_id, vgesture_command, sensitivity, dark_mode, background_color)
            VALUES (?, ?, ?, ?, ?)
        """, (
            data['id'], "", 20, 0, '#ffffff'
        ))

        conn.commit()
        conn.close()
        return jsonify({"status": "success"})
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"status": "fail", "message": str(e)}), 500

# --- 설정 조회 API ---
@app.route('/api/settings/<user_id>', methods=['GET'])
def get_settings(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT user_id, vgesture_command, sensitivity, dark_mode, background_color
        FROM settings WHERE user_id = ?
    """, (user_id,))
    row = cur.fetchone()
    conn.close()

    if row:
        keys = ['user_id', 'vgesture_command', 'sensitivity', 'dark_mode', 'background_color']
        return jsonify({"status": "success", "settings": dict(zip(keys, row))})
    else:
        return jsonify({"status": "fail", "message": "설정 정보 없음"}), 404

# --- 설정 저장 API ---@app.route('/api/settings/<user_id>', methods=['POST'])
def save_settings(user_id):
    data = request.get_json()
    print(f"save_settings called for user_id={user_id} with data={data}")
    
    if not data:
        return jsonify({"status": "fail", "message": "설정 데이터 없음"}), 400

    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM settings WHERE user_id = ?", (user_id,))
        exists = cur.fetchone()
        print("settings 존재 여부:", exists is not None)

        if exists:
            cur.execute("""
                UPDATE settings
                SET vgesture_command = ?, sensitivity = ?, dark_mode = ?, background_color = ?
                WHERE user_id = ?
            """, (
                data.get("vgesture_command", ""),
                data.get("sensitivity", 20),
                int(data.get("dark_mode", False)),
                data.get("background_color", "#ffffff"),
                user_id
            ))
        else:
            cur.execute("""
                INSERT INTO settings (user_id, vgesture_command, sensitivity, dark_mode, background_color)
                VALUES (?, ?, ?, ?, ?)
            """, (
                user_id,
                data.get("vgesture_command", ""),
                data.get("sensitivity", 20),
                int(data.get("dark_mode", False)),
                data.get("background_color", "#ffffff")
            ))

        conn.commit()
        conn.close()
        print("설정 저장 완료")
        return jsonify({"status": "success", "message": "설정 저장 완료"})

    except Exception as e:
        print("설정 저장 중 에러:", e)
        return jsonify({"status": "fail", "message": str(e)}), 500


# --- 서버 시작 ---
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)

print("BASE_DIR:", BASE_DIR)
print("Working Dir:", os.getcwd())
print("DB Path:", DB_PATH)
