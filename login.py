import tkinter as tk
from tkinter import ttk, messagebox
import hashlib
import requests
import subprocess
import sys
import os

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- 로그인 요청 ---

SERVER_IP = "123.45.67.89"  # 실제 서버 IP 또는 도메인
SERVER_PORT = 8080
BASE_URL = f"http://{SERVER_IP}:{SERVER_PORT}/api"

def login():
    user_id = entry_login_id.get()
    user_pw = entry_login_pw.get()
    hashed_pw = hash_password(user_pw)

    try:
        response = requests.post(f"{BASE_URL}/login", json={
            "username": user_id,
            "password": hashed_pw
        })

        result = response.json()
        if result.get("status") == "success":
            launch_main_program()
        else:
            messagebox.showerror("로그인 실패", "아이디 또는 비밀번호가 틀렸습니다.")
    except requests.exceptions.RequestException as e:
        messagebox.showerror("서버 오류", f"서버 연결 실패: {e}")

# --- 회원가입 요청 ---
def submit_registration():
    name = entry_name.get()
    phone = entry_phone.get()
    email = entry_email.get()
    user_id = entry_id.get()
    password = entry_pw.get()
    confirm_pw = entry_confirm.get()

    if not all([name, phone, email, user_id, password, confirm_pw]):
        messagebox.showerror("입력 오류", "모든 항목을 입력해주세요.")
        return
    if password != confirm_pw:
        messagebox.showerror("비밀번호 오류", "비밀번호가 일치하지 않습니다.")
        return

    try:
        response = requests.post("http://localhost:5000/api/register", json={
            "id": user_id,
            "name": name,
            "phone": phone,
            "email": email,
            "password": hash_password(password)
        })
        result = response.json()
        if result.get("status") == "success":
            messagebox.showinfo("회원가입 완료", "회원가입 성공!\n로그인 화면으로 이동합니다.")
            show_login_screen()
        else:
            messagebox.showerror("회원가입 실패", result.get("message", "알 수 없는 오류"))
    except requests.exceptions.RequestException as e:
        messagebox.showerror("서버 오류", f"서버 연결 실패: {e}")

# --- 프로그램 실행 ---
def launch_main_program():
    root.withdraw()
    loading = tk.Toplevel(root)
    loading.title("로딩 중...")
    loading.geometry("300x150")
    loading.configure(bg="#1e1e1e")
    tk.Label(loading, text="프로그램을 시작합니다...", fg="white", bg="#1e1e1e", font=("맑은 고딕", 12)).pack(pady=30)
    progress = ttk.Progressbar(loading, mode='indeterminate')
    progress.pack(pady=10, padx=20, fill="x")
    progress.start(10)
    def open_main():
        loading.destroy()
        subprocess.Popen([sys.executable, "main.py"], cwd=os.path.dirname(__file__))
    loading.after(3000, open_main)

# --- 화면 구성 ---
def show_login_screen():
    setup_window("로그인", 500, 600)
    frame = create_frame()
    tk.Label(frame, text="PC Gesture Control", font=("맑은 고딕", 24, "bold"), fg="#4CAF50", bg="#1f1f1f").pack(pady=(0, 30))
    global entry_login_id, entry_login_pw
    entry_login_id = make_entry(frame, "아이디")
    entry_login_pw = make_entry(frame, "비밀번호", show="*")
    make_button(frame, "로그인", login, "#4CAF50", "#66BB6A")
    make_button(frame, "회원가입", show_register_screen, "#2196F3", "#42A5F5")

def show_register_screen():
    setup_window("회원가입", 500, 700)
    frame = create_frame()
    tk.Label(frame, text="회원가입", font=("맑은 고딕", 24, "bold"), fg="#4CAF50", bg="#1f1f1f").pack(pady=(0, 30))
    global entry_name, entry_phone, entry_email, entry_id, entry_pw, entry_confirm
    entry_name = make_entry(frame, "이름")
    entry_phone = make_entry(frame, "전화번호")
    entry_email = make_entry(frame, "이메일")
    entry_id = make_entry(frame, "아이디")
    entry_pw = make_entry(frame, "비밀번호", show="*")
    entry_confirm = make_entry(frame, "비밀번호 확인", show="*")
    make_button(frame, "가입하기", submit_registration, "#4CAF50", "#66BB6A")
    make_button(frame, "뒤로가기", show_login_screen, "#9E9E9E", "#BDBDBD")

def setup_window(title, width, height):
    clear_screen()
    root.title(title)
    root.geometry(f"{width}x{height}")
    root.configure(bg="#121212")

def create_frame():
    frame = tk.Frame(root, bg="#1f1f1f", padx=30, pady=30)
    frame.place(relx=0.5, rely=0.5, anchor="center")
    return frame

def make_entry(parent, label_text, show=None):
    tk.Label(parent, text=label_text, font=("맑은 고딕", 12), fg="white", bg="#1f1f1f").pack(anchor="w", pady=(10,0))
    entry = tk.Entry(parent, font=("맑은 고딕", 12), bg="#2e2e2e", fg="white", insertbackground="white", relief="flat", highlightthickness=1, highlightbackground="#4CAF50", show=show)
    entry.pack(fill="x", pady=5)
    return entry

def make_button(parent, text, command, color, hover_color):
    btn = tk.Button(parent, text=text, command=command, font=("맑은 고딕", 12), bg=color, fg="white", relief="flat", height=2)
    btn.pack(pady=10, fill="x")
    btn.bind("<Enter>", lambda e: btn.config(bg=hover_color))
    btn.bind("<Leave>", lambda e: btn.config(bg=color))

def clear_screen():
    for widget in root.winfo_children():
        widget.destroy()

def on_closing():
    root.destroy()
    sys.exit()

def fade_in(window):
    alpha = 0
    def _increase_alpha():
        nonlocal alpha
        alpha += 0.05
        if alpha <= 1.0:
            window.attributes('-alpha', alpha)
            window.after(30, _increase_alpha)
    window.attributes('-alpha', 0)
    _increase_alpha()

# --- 실행 ---
root = tk.Tk()
setup_window("로그인", 500, 600)
root.protocol("WM_DELETE_WINDOW", on_closing)
fade_in(root)
show_login_screen()
root.mainloop()
