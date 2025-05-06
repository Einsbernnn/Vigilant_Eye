#! /usr/bin/python

from flask import Flask, Response
from imutils.video import VideoStream
import face_recognition
import imutils
import pickle
import time
import cv2
import threading

# GPIO setup for Raspberry Pi
try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    BUZZER_PIN = 17
    GPIO.setup(BUZZER_PIN, GPIO.OUT)
    HAS_GPIO = True
except (ImportError, RuntimeError):
    HAS_GPIO = False

def beep(times=1, duration=0.5):
    """Buzzer beep function"""
    if not HAS_GPIO:
        return
    for _ in range(times):
        GPIO.output(BUZZER_PIN, GPIO.HIGH)
        time.sleep(duration)
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        time.sleep(0.2)

# Play 3 short beeps at boot
threading.Thread(target=beep, args=(3, 0.2)).start()

# Load encodings
encodingsP = "encodings.pickle"
print("[INFO] loading encodings + face detector...")
data = pickle.loads(open(encodingsP, "rb").read())

app = Flask(__name__)

vs = VideoStream(src=0, framerate=10).start()
time.sleep(2.0)

currentname = "unknown"
last_beep_time = 0
beep_lock = threading.Lock()

def recognize_and_draw(frame):
    global currentname, last_beep_time
    boxes = face_recognition.face_locations(frame)
    encodings = face_recognition.face_encodings(frame, boxes)
    names = []

    now = time.time()
    name_detected_this_frame = "unknown"

    for encoding in encodings:
        matches = face_recognition.compare_faces(data["encodings"], encoding)
        name = "Unknown"
        if True in matches:
            matchedIdxs = [i for (i, b) in enumerate(matches) if b]
            counts = {}
            for i in matchedIdxs:
                name = data["names"][i]
                counts[name] = counts.get(name, 0) + 1
            name = max(counts, key=counts.get)
        names.append(name)
        name_detected_this_frame = name  # We assume only 1 face for beep logic

    # Draw boxes and names
    for ((top, right, bottom, left), name) in zip(boxes, names):
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 225), 2)
        y = top - 15 if top - 15 > 15 else top + 15
        cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX, .8, (0, 255, 255), 2)

    with beep_lock:
        if name_detected_this_frame != currentname:
            currentname = name_detected_this_frame
            if currentname == "Unknown":
                threading.Thread(target=beep, args=(3, 1)).start()
            else:
                threading.Thread(target=beep, args=(1, 1)).start()
            last_beep_time = now

    return frame

def gen_frames():
    while True:
        frame = vs.read()
        frame = imutils.resize(frame, width=500)
        frame = recognize_and_draw(frame)
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video')
def video():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5002)
    finally:
        if HAS_GPIO:
            GPIO.cleanup()
