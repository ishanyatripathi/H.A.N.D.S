import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import time
from math import hypot
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# ========== Setup ==========
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
volMin, volMax = volume.GetVolumeRange()[:2]

mpHands = mp.solutions.hands
hands = mpHands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mpDraw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(1)
screen_w, screen_h = pyautogui.size()
cv2.namedWindow("Gesture Mouse", cv2.WINDOW_NORMAL)

volume_enabled = False
prev_x, prev_y = 0, 0
smooth_factor = 0.9
scroll_center_y = 240
scroll_sensitivity = 2
last_scroll_time = 0
scroll_delay = 0.2
last_click_time = 0
click_cooldown = 0.1
last_zoom = None
last_zoom_time = 0
zoom_delay = 0.3
swipe_cooldown = 1.5
p_time = 0
button_coords = (10, 10, 210, 60)

swipe_state = {
    'previous_side': None,
    'last_swipe_time': 0
}

cv2.setMouseCallback("Gesture Mouse", lambda event, x, y, flags, param: toggle_volume_mode(event, x, y))

def toggle_volume_mode(event, x, y):
    global volume_enabled
    x1, y1, x2, y2 = button_coords
    if event == cv2.EVENT_LBUTTONDOWN and x1 <= x <= x2 and y1 <= y <= y2:
        volume_enabled = not volume_enabled

def interpolate(val, src_range, dst_range):
    return np.interp(val, src_range, dst_range)

def debounce(last_time, cooldown):
    return (time.time() - last_time) > cooldown

def fingers_extended(lmDict, fingers):
    if 0 not in lmDict: return [False] * len(fingers)
    wrist_y = lmDict[0][1]
    return [lmDict[f][1] < wrist_y if f in lmDict else False for f in fingers]

def volume_mode(lmDict_left):
    if 4 in lmDict_left and 8 in lmDict_left:
        x1, y1 = lmDict_left[4]
        x2, y2 = lmDict_left[8]
        length = hypot(x2 - x1, y2 - y1)
        vol = np.interp(length, [20, 200], [volMin, volMax])
        volume.SetMasterVolumeLevel(vol, None)
        vol_bar = np.interp(length, [20, 200], [400, 150])
        vol_percent = int(np.interp(length, [20, 200], [0, 100]))
        cv2.rectangle(img, (50, int(vol_bar)), (85, 400), (0, 255, 0), cv2.FILLED)
        cv2.rectangle(img, (50, 150), (85, 400), (0, 255, 0), 2)
        cv2.putText(img, f"{vol_percent}%", (40, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(img, "Volume Mode", (10, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

def normal_mode(lmDict_right, handedness_map):
    global prev_x, prev_y, last_click_time, last_zoom, last_zoom_time
    if 8 in lmDict_right:
        x, y = lmDict_right[8]
        screen_x = interpolate(x, [0, img.shape[1]], [0, screen_w])
        screen_y = interpolate(y, [0, img.shape[0]], [0, screen_h])
        smooth_x = prev_x + (screen_x - prev_x) * smooth_factor
        smooth_y = prev_y + (screen_y - prev_y) * smooth_factor
        pyautogui.moveTo(smooth_x, smooth_y)
        prev_x, prev_y = smooth_x, smooth_y
        cv2.putText(img, 'Mouse Moving', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

    if 4 in lmDict_right and 8 in lmDict_right:
        dist = hypot(lmDict_right[4][0] - lmDict_right[8][0], lmDict_right[4][1] - lmDict_right[8][1])
        if dist < 20 and debounce(last_click_time, click_cooldown):
            pyautogui.click()
            last_click_time = time.time()
            cv2.putText(img, 'Click', (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    if 'Left' in handedness_map and 8 in handedness_map['Left'] and 8 in lmDict_right:
        x1, y1 = handedness_map['Left'][8]
        x2, y2 = lmDict_right[8]
        zoom_dist = hypot(x2 - x1, y2 - y1)
        zoom_val = np.interp(zoom_dist, [50, 300], [-20, 20])
        if last_zoom is not None and debounce(last_zoom_time, zoom_delay):
            delta = int((zoom_val - last_zoom) * 0.1)
            if delta > 0:
                pyautogui.hotkey('ctrl', '+')
                cv2.putText(img, 'Zooming In', (10, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            elif delta < 0:
                pyautogui.hotkey('ctrl', '-')
                cv2.putText(img, 'Zooming Out', (10, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            last_zoom_time = time.time()
        last_zoom = zoom_val

def handle_scroll(lmDict_left):
    global last_scroll_time
    if 8 in lmDict_left and debounce(last_scroll_time, scroll_delay):
        y = lmDict_left[8][1]
        delta = (scroll_center_y - y) / scroll_sensitivity
        pyautogui.scroll(int(delta))
        last_scroll_time = time.time()
        cv2.putText(img, f"Scroll: {int(delta)}", (10, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)

def handle_swipe_cross_center(lmDict_right):
    global swipe_state
    center_x = img.shape[1] // 2
    if 8 in lmDict_right:
        x = lmDict_right[8][0]
        side = 'left' if x < center_x else 'right'

        if swipe_state['previous_side'] and swipe_state['previous_side'] != side:
            if debounce(swipe_state['last_swipe_time'], swipe_cooldown):
                if side == 'right':
                    pyautogui.press('nexttrack')
                    cv2.putText(img, 'Next Song', (10, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)
                else:
                    pyautogui.press('prevtrack')
                    cv2.putText(img, 'Prev Song', (10, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)
                swipe_state['last_swipe_time'] = time.time()

        swipe_state['previous_side'] = side

while True:
    success, img = cap.read()
    if not success:
        break

    img = cv2.flip(img, 1)
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(imgRGB)

    h, w, _ = img.shape
    handedness_map = {}
    lmDict_right = {}
    lmDict_left = {}

    if results.multi_hand_landmarks and results.multi_handedness:
        for idx, (hand_landmark, hand_handedness) in enumerate(zip(results.multi_hand_landmarks, results.multi_handedness)):
            label = hand_handedness.classification[0].label
            lmDict = {}
            for id, lm in enumerate(hand_landmark.landmark):
                lmDict[id] = (int(lm.x * w), int(lm.y * h))
            handedness_map[label] = lmDict
            if label == 'Right':
                lmDict_right = lmDict
            else:
                lmDict_left = lmDict
            mpDraw.draw_landmarks(img, hand_landmark, mpHands.HAND_CONNECTIONS)

    x1, y1, x2, y2 = button_coords
    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255) if volume_enabled else (0, 255, 0), cv2.FILLED)
    mode_text = "Volume Mode" if volume_enabled else "Normal Mode"
    cv2.putText(img, mode_text, (x1 + 10, y1 + 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    center_x = img.shape[1] // 2
    cv2.line(img, (center_x, 0), (center_x, img.shape[0]), (255, 255, 255), 2)

    if volume_enabled:
        if lmDict_left:
            volume_mode(lmDict_left)
        if lmDict_right:
            normal_mode(lmDict_right, {})
    else:
        if lmDict_right:
            normal_mode(lmDict_right, handedness_map)
            handle_swipe_cross_center(lmDict_right)
        if lmDict_left:
            handle_scroll(lmDict_left)

    c_time = time.time()
    fps = 1 / (c_time - p_time) if c_time != p_time else 0
    p_time = c_time
    cv2.putText(img, f'FPS: {int(fps)}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 3)

    cv2.imshow("Gesture Mouse", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
