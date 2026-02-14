import cv2
import mediapipe as mp
import time
import requests
import webbrowser
import pyautogui
import numpy as np

BASE_URL = "http://127.0.0.1:5000"

# -------------------------------
# FACE MESH for EMOTION RECOGNITION
# -------------------------------
mp_face = mp.solutions.face_mesh
face_mesh = mp_face.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.6
)

# -------------------------------
# HAND DETECTION
# -------------------------------
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)


# -------------------------------
# EMOTION DETECTION
# -------------------------------
def detect_emotion(face_landmarks, frame_w, frame_h):
    left = face_landmarks.landmark[61]
    right = face_landmarks.landmark[291]
    top = face_landmarks.landmark[13]
    bottom = face_landmarks.landmark[14]

    mouth_width = abs(right.x - left.x)
    mouth_height = abs(bottom.y - top.y)

    ratio = mouth_height / mouth_width

    if ratio > 0.32:
        return "Happy"
    elif ratio < 0.18:
        return "Sad"
    else:
        return "Neutral"


# -------------------------------
# GESTURE DETECTION
# -------------------------------
def detect_gesture(hand_landmarks):
    finger_tips = [8, 12, 16, 20]
    thumb_tip = 4

    fingers = []

    # thumb check
    thumb_y = hand_landmarks.landmark[thumb_tip].y
    thumb_base_y = hand_landmarks.landmark[2].y

    if thumb_y < thumb_base_y:
        thumb_status = "Thumb Up"
    elif thumb_y > thumb_base_y:
        thumb_status = "Thumb Down"
    else:
        thumb_status = ""

    # normal thumb direction
    if hand_landmarks.landmark[thumb_tip].x < hand_landmarks.landmark[thumb_tip - 1].x:
        fingers.append(1)
    else:
        fingers.append(0)

    # other fingers
    for tip in finger_tips:
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
            fingers.append(1)
        else:
            fingers.append(0)

    total = fingers.count(1)

    if total == 0:
        return "Fist"
    if total == 5:
        return "Palm"
    if total == 2:
        return "Two Fingers"
    if total == 1 and fingers[1] == 1:
        return "Index Finger"
    if total == 3:
        return "Three Fingers"
    if thumb_status == "Thumb Up":
        return "Thumb Up"
    if thumb_status == "Thumb Down":
        return "Thumb Down"

    return "Unknown"


# -------------------------------
# PERFORM ACTION
# -------------------------------
def perform_action(task, option, gesture):
    print(f"[ACTION] task={task}, option={option}, gesture={gesture}")

    if task == "perform":

        if option == "open_website":
            if gesture == "Palm":
                webbrowser.open("https://youtube.com")
            elif gesture == "Fist":
                webbrowser.open("https://google.com")
            elif gesture == "Two Fingers":
                webbrowser.open("https://chat.openai.com/")
            elif gesture == "Index Finger":
                webbrowser.open("https://geeksforgeeks.org")
            elif gesture == "Thumb Up":
                webbrowser.open("https://mail.google.com")

        elif option == "keyboard_action":
            if gesture == "Palm":
                pyautogui.press("volumemute")
            elif gesture == "Fist":
                pyautogui.hotkey("win", "printscreen")
            elif gesture == "Two Fingers":
                pyautogui.press("volumeup")
            elif gesture == "Three Fingers":
                pyautogui.press("volumedown")
            elif gesture == "Thumb Up":
                pyautogui.press("brightnessup")
            elif gesture == "Thumb Down":
                pyautogui.press("brightnessdown")
            elif gesture == "Index Finger":
                pyautogui.press("capslock")


# -------------------------------
# SEND DATA TO FLASK
# -------------------------------
def send_detected(data):
    try:
        requests.post(f"{BASE_URL}/gesture_detected",
                      json={"data": data}, timeout=1)
    except:
        pass


def get_task():
    try:
        r = requests.get(f"{BASE_URL}/get_task", timeout=1)
        return r.json()
    except:
        return {"task": None, "option": None}


# -------------------------------
# MAIN LOOP
# -------------------------------
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Cannot open camera.")
    exit()

print("✅ Camera Running...")


while True:
    ret, frame = cap.read()
    if not ret:
        break

    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    hand_result = hands.process(rgb)
    face_result = face_mesh.process(rgb)

    current = get_task()
    task = current["task"]
    option = current["option"]

    # -----------------------
    # CHATBOT MODE (MERGED FROM FIRST CODE)
    # -----------------------
    if task == "chatbot":
        cv2.putText(frame, "Chatbot Active...", (10, 95),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 200, 255), 2)

        send_detected("chatbot_active")
        time.sleep(0.5)

    # -----------------------
    # FACE EMOTION MODE
    # -----------------------
    if task == "emotion":
        if face_result.multi_face_landmarks:
            for faceLms in face_result.multi_face_landmarks:

                emotion = detect_emotion(faceLms, w, h)

                cv2.putText(frame, f"Emotion: {emotion}", (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)

                send_detected(emotion)
                time.sleep(1)

    # -----------------------
    # HAND MODE
    # -----------------------
    if hand_result.multi_hand_landmarks:
        for handLms in hand_result.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, handLms, mp_hands.HAND_CONNECTIONS)

            gesture = detect_gesture(handLms)

            cv2.putText(frame, gesture, (10, 140),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 0, 0), 3)

            if gesture != "Unknown":
                send_detected(gesture)
                perform_action(task, option, gesture)
                time.sleep(1)

    cv2.putText(frame, f"Task: {task}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

    cv2.imshow("Detector", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
