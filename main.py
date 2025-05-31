import sys
import threading
from PyQt6.QtWidgets import QApplication
from ui import GestureControlUI
from gesture_control import GestureControl

def start_gesture_recognition(gesture_control):
    """제스처 인식을 별도 스레드로 실행"""
    gesture_control.run()

def main():
    app = QApplication(sys.argv)
    window = GestureControlUI()

    gesture_control = GestureControl(window)
    gesture_thread = threading.Thread(
        target=start_gesture_recognition, 
        args=(gesture_control,), 
        daemon=True
    )
    gesture_thread.start()

    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
