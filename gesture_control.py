import cv2
import mediapipe as mp
import pyautogui
import math
import numpy as np
import time
import subprocess
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt

class GestureControl:
    def __init__(self, ui):
        self.ui = ui
        self.cap = cv2.VideoCapture(0)
        print("카메라를 열 수 없습니다.")
        self.screen_w, self.screen_h = pyautogui.size()

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils

        self.mode = None
        self.activation_start = None
        self.switch_start = None
        self.thumb_hold_start = None
        self.last_click_time = 0
        self.dragging = False
        self.prev_x, self.prev_y = pyautogui.position()

    def lerp(self, a, b, t):
        return a + (b - a) * t

    def calibrate(self):
        self.ui.update_log("손바닥을 펼쳐 캘리브레이션 중...")
        calibration_start = None

        while True:
            ret, frame = self.cap.read()
            if not ret:
                continue
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb)

            if results.multi_hand_landmarks:
                hand_landmarks = results.multi_hand_landmarks[0]
                lm = hand_landmarks.landmark

                open_palm = all(
                    lm[i].y < lm[i-2].y for i in [8, 12, 16, 20]
                )

                if open_palm:
                    if calibration_start is None:
                        calibration_start = time.time()
                    elif time.time() - calibration_start >= 2.0:
                        self.ui.update_log("캘리브레이션 완료")
                        return
                else:
                    calibration_start = None

            # 캘리브레이션 화면도 UI에 띄움
            self.update_camera_frame(frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break

    def run(self):
        self.calibrate()
        self.ui.update_log("제스처 모드 대기 중...")

        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb)

            if results.multi_hand_landmarks:
                hand_landmarks = results.multi_hand_landmarks[0]
                landmarks = [(l.x, l.y, l.z) for l in hand_landmarks.landmark]

                now = time.time()

                if self.is_gun_pose(landmarks):
                    if self.activation_start is None:
                        self.activation_start = now
                    elif now - self.activation_start >= 2.0:
                        if self.mode != "mouse":
                            self.mode = "mouse"
                            self.ui.update_log("마우스 이동 모드로 전환")
                            self.ui.update_mode("마우스 이동 모드")
                        self.activation_start = None
                elif self.is_open_palm(landmarks):
                    if self.switch_start is None:
                        self.switch_start = now
                    elif now - self.switch_start >= 2.0:
                        if self.mode != "gesture":
                            self.mode = "gesture"
                            self.ui.update_log("일반 제스처 모드로 전환")
                            self.ui.update_mode("일반 제스처 모드")
                        self.switch_start = None
                else:
                    self.activation_start = None
                    self.switch_start = None

                if self.mode == "mouse":
                    self.handle_mouse_mode(landmarks)
                elif self.mode == "gesture":
                    self.handle_gesture_mode(landmarks)

                self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

            # 🔥 여기서 매 프레임마다 UI에 업데이트
            self.update_camera_frame(frame)

            if cv2.waitKey(1) & 0xFF == 27:
                break

        self.cap.release()

    def update_camera_frame(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        p = convert_to_Qt_format.scaled(640, 480, aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio)
        self.ui.camera_label.setPixmap(QPixmap.fromImage(p))

    def handle_mouse_mode(self, landmarks):
        tip2d, base2d = landmarks[8][:2], landmarks[5][:2]
        dx, dy = tip2d[0]-base2d[0], tip2d[1]-base2d[1]
        target_x = tip2d[0] + dx * 2
        target_y = tip2d[1] + dy * 2

        screen_x = int(target_x * self.screen_w)
        screen_y = int(target_y * self.screen_h)

        sensitivity = self.ui.get_sensitivity()
        smooth_x = self.lerp(self.prev_x, screen_x, sensitivity)
        smooth_y = self.lerp(self.prev_y, screen_y, sensitivity)
        pyautogui.moveTo(smooth_x, smooth_y)
        self.prev_x, self.prev_y = smooth_x, smooth_y

        thumb_tip = landmarks[4]
        index_base = landmarks[5]
        thumb_index_distance = math.sqrt(
            (thumb_tip[0] - index_base[0]) ** 2 + (thumb_tip[1] - index_base[1]) ** 2
        )

        click_threshold = 0.035
        now = time.time()

        if thumb_index_distance < click_threshold:
            if self.thumb_hold_start is None:
                self.thumb_hold_start = now
            elif not self.dragging and (now - self.thumb_hold_start) >= 2.0:
                pyautogui.mouseDown(button='left')
                self.dragging = True
                self.ui.update_log("드래그 시작")
        else:
            if self.dragging:
                pyautogui.mouseUp(button='left')
                self.dragging = False
                self.ui.update_log("드래그 종료")
            elif self.thumb_hold_start is not None:
                if (now - self.thumb_hold_start) < 2.0 and (now - self.last_click_time) > 1.0:
                    pyautogui.click(button='left')
                    self.last_click_time = now
                    self.ui.update_log("클릭 완료")
            self.thumb_hold_start = None

    def handle_gesture_mode(self, landmarks):
        if self.is_fist(landmarks):
            pyautogui.press("volumeup")
            self.ui.update_log("볼륨업 실행")
            time.sleep(0.5)
        elif self.is_pinky_only(landmarks):
            pyautogui.press("volumedown")
            self.ui.update_log("볼륨다운 실행")
            time.sleep(0.5)
        elif self.is_v_pose(landmarks):
            vgesture_command = self.ui.vgesture_command_line.text()
            if vgesture_command:
                self.ui.update_log(f"V자 감지: {vgesture_command} 실행")
                subprocess.Popen(vgesture_command, shell=True)
                time.sleep(2)

    def is_gun_pose(self, landmarks):
        idx, mid, thm = landmarks[8], landmarks[12], landmarks[4]
        idx_base, mid_base, thm_base = landmarks[6], landmarks[10], landmarks[3]
        ring, pinky = landmarks[16], landmarks[20]

        return (
            idx[1] < idx_base[1] and
            mid[1] < mid_base[1] and
            thm[1] < thm_base[1] and
            abs(idx[0] - mid[0]) < 0.03 and
            ring[1] > landmarks[14][1] and
            pinky[1] > landmarks[18][1]
        )

    def is_open_palm(self, landmarks):
        return all(landmarks[i][1] < landmarks[i-2][1] for i in [8, 12, 16, 20])

    def is_v_pose(self, landmarks):
        idx, mid, thm = landmarks[8], landmarks[12], landmarks[4]
        idx_base = landmarks[5]
        return (
            abs(idx[0] - mid[0]) > 0.05 and
            math.hypot(thm[0] - idx_base[0], thm[1] - idx_base[1]) < 0.04
        )

    def is_fist(self, landmarks):
        return all(landmarks[tip][1] > landmarks[tip-2][1] for tip in [8, 12, 16, 20])

    def is_pinky_only(self, landmarks):
        return (
            landmarks[8][1] > landmarks[6][1] and
            landmarks[12][1] > landmarks[10][1] and
            landmarks[16][1] > landmarks[14][1] and
            landmarks[20][1] < landmarks[18][1]
        )
