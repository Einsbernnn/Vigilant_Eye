#!/usr/bin/python
#Camera_API_FD_May21.py
#dev by EinsbernSystems

from flask import Flask, Response, request, jsonify
from imutils.video import VideoStream
import face_recognition
import imutils
import pickle
import time
import cv2
import threading
import numpy as np
import os
from datetime import datetime
import glob
import atexit
import platform
import subprocess
from telegram import Bot
from telegram.ext import CommandHandler, Updater, MessageHandler, Filters
import json
from re import sub
import re

app = Flask(__name__)

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    BUZZER_PIN = 17
    SERVO_PIN = 23
    PIR_PIN = 22
    LED_PIN = 12  # GPIO12 for LED flickering
    GPIO.setup(BUZZER_PIN, GPIO.OUT)
    GPIO.setup(SERVO_PIN, GPIO.OUT)
    GPIO.setup(PIR_PIN, GPIO.IN)
    GPIO.setup(LED_PIN, GPIO.OUT)  # Setup LED
    servo = GPIO.PWM(SERVO_PIN, 50)  # 50Hz for servo
    servo.start(0)
    HAS_GPIO = True
except (ImportError, RuntimeError):
    HAS_GPIO = False

# State for enabling/disabling buzzer, motion sensor, LED, and servo
buzzer_enabled = True
motion_sensor_enabled = True
servo_enabled = True
led_enabled = True

# Add state for intruder detection
intruder_active = False
intruder_last_seen = 0

# Telegram Bot setup
TELEGRAM_BOT_TOKEN = "7804374963:AAFoeQzLc9k95qPn5f_xKrsTAwY80J6kRVY"
TELEGRAM_CHAT_ID = "-4656082952"
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Track last notifications to avoid spamming
last_notification_time = {}
NOTIFICATION_COOLDOWN = 60  # seconds between notifications for the same person

def send_telegram_notification(message):
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        print(f"[INFO] Telegram notification sent: {message}")
    except Exception as e:
        print(f"[ERROR] Failed to send Telegram notification: {e}")

@app.route('/set-buzzer', methods=['POST'])
def set_buzzer():
    global buzzer_enabled
    data = request.get_json(force=True, silent=True)
    if data and 'enabled' in data:
        buzzer_enabled = bool(data['enabled'])
        return jsonify({'buzzer_enabled': buzzer_enabled}), 200
    return jsonify({'error': 'Missing enabled field'}), 400

@app.route('/set-motion-sensor', methods=['POST'])
def set_motion_sensor():
    global motion_sensor_enabled
    data = request.get_json(force=True, silent=True)
    if data and 'enabled' in data:
        motion_sensor_enabled = bool(data['enabled'])
        return jsonify({'motion_sensor_enabled': motion_sensor_enabled}), 200
    return jsonify({'error': 'Missing enabled field'}), 400

# Set LED enable/disable
@app.route('/set-led', methods=['POST'])
def set_led():
    global led_enabled
    data = request.get_json(force=True, silent=True)
    if data and 'enabled' in data:
        led_enabled = bool(data['enabled'])
        return jsonify({'led_enabled': led_enabled}), 200
    return jsonify({'error': 'Missing enabled field'}), 400

# Flicker the LED
def flicker_led():
    if HAS_GPIO and led_enabled:
        for _ in range(3):  # Flicker 3 times
            GPIO.output(LED_PIN, GPIO.HIGH)
            time.sleep(0.2)
            GPIO.output(LED_PIN, GPIO.LOW)
            time.sleep(0.2)

# Buzzer beep function
# Only beep if buzzer_enabled is True
def beep(times=1, duration=0.2):
    if not HAS_GPIO or not buzzer_enabled:
        return
    for _ in range(times):
        GPIO.output(BUZZER_PIN, GPIO.HIGH)
        time.sleep(duration)
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        time.sleep(0.2)

# PIR sensor notification state
pir_last_state = False
pir_triggered_time = 0
pir_notified = False
pir_notification_message = None

def pir_monitor_thread():
    global pir_last_state, pir_triggered_time, pir_notified, pir_notification_message, last_notification_time
    if not HAS_GPIO:
        return
    while True:
        pir_state = GPIO.input(PIR_PIN)
        now = time.time()
        if pir_state and motion_sensor_enabled:
            if not pir_last_state:  # Rising edge: motion just detected
                pir_triggered_time = now
                pir_notified = False
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                camera_location = None
                try:
                    with open('camera_location.txt', 'r') as f:
                        camera_location = f.read().strip()
                except Exception:
                    camera_location = None
                location_str = f" at your {camera_location}" if camera_location else ""
                # PIR motion notification anti-spam
                if now - last_notification_time.get('pir_motion', 0) > NOTIFICATION_COOLDOWN:
                    pir_notification_message = f"Motion detected{location_str} at {timestamp}"
                    send_telegram_notification(pir_notification_message)
                    last_notification_time['pir_motion'] = now
                # Log motion event
                log_detection_event('motion', now - (recording_start_time or now), {})
                flicker_led()
        else:
            pir_triggered_time = 0
            pir_notified = False
            pir_notification_message = None
        pir_last_state = pir_state
        time.sleep(0.5)

if HAS_GPIO:
    threading.Thread(target=pir_monitor_thread, daemon=True).start()

class NonMirroredTracker:
    def __init__(self):
        self.last_move_time = time.time()
        self.move_delay = 0.15  # Minimum time between moves
        self.tracking_threshold = 0.25  # 25% from center

    def should_move(self, offset, frame_width):
        # Calculate normalized offset (-1 to 1)
        norm_offset = offset / (frame_width * self.tracking_threshold)
        return abs(norm_offset) > 1

    def move_servo(self, offset, frame_width):
        if not HAS_GPIO or time.time() - self.last_move_time < self.move_delay:
            return

        # Calculate direction (corrected for mirrored camera)
        if offset > 0:
            # Face appears to the right in mirrored view - actually move left
            duty_cycle = 6.5  # Move left (adjust for your servo)
        else:
            # Face appears to the left in mirrored view - actually move right
            duty_cycle = 8.5  # Move right (adjust for your servo)

        # Apply movement
        servo.ChangeDutyCycle(duty_cycle)
        time.sleep(0.1)
        servo.ChangeDutyCycle(0)
        self.last_move_time = time.time()

# Initialize tracker
tracker = NonMirroredTracker()

# Load face encodings
encodingsP = "encodings.pickle"
print("[INFO] loading encodings + face detector...")
data = pickle.loads(open(encodingsP, "rb").read())

vs = VideoStream(src=0, framerate=10).start()
time.sleep(2.0)

currentname = "unknown"
last_beep_time = 0
beep_lock = threading.Lock()

# 3 short beeps on boot
threading.Thread(target=beep, args=(3, 0.2)).start()

VIDEO_DIR = '/media/einsbern/76E8-CACF/footage_fd'
recording = False
recording_writer = None
recording_folder = None
recording_filename = None
recording_lock = threading.Lock()
recording_pending = False
pending_recording_info = {}
last_frame_size = (500, 500)  # Default, will be updated dynamically
recording_start_time = None
recording_frame_count = 0

# Helper to get formatted folder name
# Use only safe characters for folder and file names
def get_recording_folder_name():
    now = datetime.now()
    # Use YYYY-MM-DD_HH-MM-SS format
    return now.strftime('%Y-%m-%d_%H-%M-%S')

def get_unique_recording_folder_name():
    base_name = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    folder_path = os.path.join(VIDEO_DIR, base_name)
    counter = 1
    unique_name = base_name
    while os.path.exists(folder_path):
        unique_name = f"{base_name}_{counter}"
        folder_path = os.path.join(VIDEO_DIR, unique_name)
        counter += 1
    return unique_name

def get_next_video_filename(folder_path):
    now = datetime.now()
    # Use YYYY-MM-DD_HH-MM-SS format
    if platform.system() == 'Windows':
        filename = now.strftime('%Y-%m-%d_%H-%M-%S') + '.avi'
    else:
        filename = now.strftime('%Y-%m-%d_%H-%M-%S') + '.mov'
    return filename

def get_log_path(folder_name, video_filename):
    folder_name = sanitize_filename(folder_name)
    video_filename = sanitize_filename(video_filename)
    folder_path = os.path.join(VIDEO_DIR, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    base, _ = os.path.splitext(video_filename)
    return os.path.join(folder_path, f'{base}.json')

def get_log_txt_path(folder_name, video_filename):
    folder_name = sanitize_filename(folder_name)
    video_filename = sanitize_filename(video_filename)
    folder_path = os.path.join(VIDEO_DIR, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    base, _ = os.path.splitext(video_filename)
    return os.path.join(folder_path, f'{base}.log')

def sanitize_filename(name):
    # Replace spaces, commas, colons, and other unsafe chars with '_'
    return re.sub(r'[^A-Za-z0-9._-]', '_', str(name))

@app.route('/start-recording', methods=['POST'])
def start_recording():
    global recording, recording_writer, recording_folder, recording_filename, recording_pending, pending_recording_info
    with recording_lock:
        print(f"[DEBUG] start_recording called. recording={recording}, writer={recording_writer}")
        # Hard reset: always clear previous state
        if recording_writer:
            try:
                recording_writer.release()
                print("[DEBUG] (Hard reset) VideoWriter released.")
            except Exception as e:
                print(f"[ERROR] (Hard reset) Exception releasing VideoWriter: {e}")
        recording = False
        recording_writer = None
        recording_folder = None
        recording_filename = None
        # Accept folder_name and filename from frontend
        req = request.get_json(force=True, silent=True)
        if req and 'folder_name' in req and 'filename' in req:
            folder_name = sanitize_filename(req['folder_name'])
            filename = sanitize_filename(req['filename'])
        else:
            folder_name = get_unique_recording_folder_name()
            filename = get_next_video_filename('')
        pending_recording_info = {
            'folder_name': folder_name,
            'filename': filename
        }
        recording_pending = True
        print(f"[DEBUG] Recording pending. Will start on next frame. folder={folder_name}, file={filename}")
        return jsonify({'folder': folder_name, 'filename': filename}), 200

@app.route('/stop-recording', methods=['POST'])
def stop_recording():
    global recording, recording_writer, recording_folder, recording_filename, recording_start_time, recording_frame_count
    with recording_lock:
        print(f"[DEBUG] stop_recording called. recording={recording}, writer={recording_writer}")
        if not recording:
            return jsonify({'error': 'Not recording'}), 400
        recording = False
        if recording_writer:
            try:
                recording_writer.release()
                print("[DEBUG] VideoWriter released.")
            except Exception as e:
                print(f"[ERROR] Exception releasing VideoWriter: {e}")
            recording_writer = None
        folder = recording_folder
        filename = recording_filename
        elapsed = None
        fps = None
        if recording_start_time is not None and recording_frame_count > 1:
            elapsed = time.time() - recording_start_time
            fps = recording_frame_count / elapsed if elapsed > 0 else 1.0
        recording_folder = None
        recording_filename = None
        recording_start_time = None
        print(f"[DEBUG] Stopped recording: folder={folder}, file={filename}, frames={recording_frame_count}, elapsed={elapsed}, fps={fps}")

        # --- ffmpeg conversion for browser compatibility and correct FPS ---
        if filename and filename.endswith('.mov'):
            folder_path = os.path.join(VIDEO_DIR, folder)
            mov_path = os.path.join(folder_path, filename)
            mp4_filename = filename.rsplit('.', 1)[0] + '.mp4'
            mp4_path = os.path.join(folder_path, mp4_filename)
            # Use calculated FPS if available, else fallback to 1.0
            real_fps = max(1.0, min(30.0, fps)) if fps else 1.0
            ffmpeg_cmd = [
                'ffmpeg', '-y', '-r', str(real_fps), '-i', mov_path,
                '-vcodec', 'libx264', '-acodec', 'aac', '-pix_fmt', 'yuv420p', mp4_path
            ]
            try:
                print(f"[DEBUG] Running ffmpeg: {' '.join(ffmpeg_cmd)}")
                subprocess.run(ffmpeg_cmd, check=True)
                print(f"[DEBUG] ffmpeg conversion complete: {mp4_path}")
                # Optionally, remove the original .mov file
                # os.remove(mov_path)
                return jsonify({'folder': folder, 'filename': mp4_filename, 'fps': real_fps}), 200
            except Exception as e:
                print(f"[ERROR] ffmpeg conversion failed: {e}")
                return jsonify({'folder': folder, 'filename': filename, 'warning': 'ffmpeg conversion failed', 'fps': real_fps}), 200
        # --- end ffmpeg conversion ---

        return jsonify({'folder': folder, 'filename': filename, 'fps': fps}), 200

@app.route('/pir-notification')
def pir_notification():
    global pir_notification_message, motion_sensor_enabled
    if not motion_sensor_enabled:
        return jsonify({'notification': None})
    if pir_notification_message:
        msg = pir_notification_message
        pir_notification_message = None  # Only send once
        return jsonify({'notification': msg})
    return jsonify({'notification': None})

@app.route('/set-servo-angle', methods=['POST'])
def set_servo_angle():
    global servo_enabled
    if not HAS_GPIO or not servo_enabled:
        return jsonify({'error': 'Servo not available'}), 400
    data = request.get_json(force=True, silent=True)
    angle = data.get('angle')
    if angle is None or not (0 <= angle <= 180):
        return jsonify({'error': 'Invalid angle'}), 400
    # Convert angle to duty cycle (adjust for your servo)
    duty_cycle = 2.5 + (angle / 180.0) * 10
    servo.ChangeDutyCycle(duty_cycle)
    time.sleep(0.3)
    servo.ChangeDutyCycle(0)
    return jsonify({'status': 'success', 'angle': angle}), 200

@app.route('/snap', methods=['POST'])
def snap_picture():
    frame = vs.read()
    filename = f"snap_{int(time.time())}.jpg"
    filepath = os.path.join('/tmp', filename)
    cv2.imwrite(filepath, frame)
    return jsonify({'status': 'success', 'filepath': filepath, 'filename': filename}), 200

@app.route('/log-event', methods=['POST'])
def log_event():
    data = request.get_json(force=True, silent=True)
    folder = data.get('folder')
    video = data.get('video')
    event_type = data.get('event_type')  # 'motion', 'unknown', 'known'
    timestamp = data.get('timestamp')    # seconds (float or int)
    extra = data.get('extra', {})
    if not (folder and video and event_type and timestamp is not None):
        return jsonify({'error': 'Missing required fields'}), 400
    log_path = get_log_path(folder, video)
    log_entry = {
        'event_type': event_type,
        'timestamp': timestamp,
        'extra': extra
    }
    logs = []
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            try:
                logs = json.load(f)
            except Exception:
                logs = []
    logs.append(log_entry)
    with open(log_path, 'w') as f:
        json.dump(logs, f)
    return jsonify({'success': True})

@app.route('/get-logs', methods=['GET'])
def get_logs():
    folder = request.args.get('folder')
    video = request.args.get('video')
    print(f"[DEBUG] /get-logs called with folder={folder}, video={video}")
    if not (folder and video):
        return jsonify({'error': 'Missing folder or video'}), 400
    log_path = get_log_txt_path(folder, video)
    print(f"[DEBUG] Looking for log_path: {log_path}")
    logs = []
    # Fallback: if .log for requested video doesn't exist, try any .log file with the same base name
    if not os.path.exists(log_path):
        folder_path = os.path.join(VIDEO_DIR, folder)
        base, _ = os.path.splitext(video)
        for fname in os.listdir(folder_path):
            if fname.startswith(base) and fname.endswith('.log'):
                log_path = os.path.join(folder_path, fname)
                print(f"[DEBUG] Fallback found log_path: {log_path}")
                break
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            for line in f:
                parts = line.strip().split('|', 2)
                if len(parts) == 3:
                    event_type, timestamp, extra_str = parts
                    try:
                        import json
                        extra = json.loads(extra_str)
                    except Exception:
                        extra = {}
                    logs.append({
                        'event_type': event_type,
                        'timestamp': float(timestamp),
                        'extra': extra
                    })
    else:
        print(f"[DEBUG] No log file found for {video} in {folder_path}")
    print(f"[DEBUG] Returning {len(logs)} log entries")
    return jsonify(logs)

def cleanup_recording():
    global recording, recording_writer
    with recording_lock:
        if recording_writer:
            recording_writer.release()
            recording_writer = None
        recording = False
atexit.register(cleanup_recording)

# Replace log_detection_event to write to .log file in video folder
def log_detection_event(event_type, timestamp, extra=None):
    if recording and recording_folder and recording_filename:
        log_path = get_log_txt_path(recording_folder, recording_filename)
        extra_str = json.dumps(extra or {})
        with open(log_path, 'a') as f:
            f.write(f"{event_type}|{timestamp}|{extra_str}\n")

def recognize_and_draw(frame):
    global currentname, last_beep_time, intruder_active, intruder_last_seen, last_notification_time

    # Convert from BGR to RGB for face_recognition
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Get current time and format it for display
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Add this before the cv2.putText() call
    text_size = cv2.getTextSize(timestamp, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
    cv2.rectangle(frame, (5, 5), (15 + text_size[0], 35), (0, 0, 0), -1)  # Black background

    # Add timestamp to the frame (top-left corner)
    cv2.putText(frame, timestamp, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # Detect faces
    boxes = face_recognition.face_locations(rgb)
    encodings = face_recognition.face_encodings(rgb, boxes)
    names = []

    frame_center = frame.shape[1] // 2
    primary_face_x = None
    largest_size = 0

    for encoding, (top, right, bottom, left) in zip(encodings, boxes):
        # Track largest face
        face_size = (right - left) * (bottom - top)
        if face_size > largest_size:
            largest_size = face_size
            primary_face_x = (left + right) // 2

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
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        y = top - 15 if top - 15 > 15 else top + 15
        cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    # Tracking logic (corrected for mirrored camera)
    if primary_face_x is not None:
        offset = primary_face_x - frame_center
        if tracker.should_move(offset, frame.shape[1]):
            tracker.move_servo(offset, frame.shape[1])

        # Visual feedback
        cv2.line(frame, (frame_center, 0), (frame_center, frame.shape[0]), (255, 0, 0), 1)
        threshold = int(frame.shape[1] * tracker.tracking_threshold)
        cv2.line(frame, (frame_center - threshold, 0),
                (frame_center - threshold, frame.shape[0]), (0, 0, 255), 1)
        cv2.line(frame, (frame_center + threshold, 0),
                (frame_center + threshold, frame.shape[0]), (0, 0, 255), 1)

    now = time.time()
    with beep_lock:
        if "Unknown" in names:
            # Flicker LED when unknown detected
            if led_enabled:
                flicker_led()
            now_time = time.time()
            # Intruder notification anti-spam
            if not intruder_active or now_time - last_notification_time.get('intruder', 0) > NOTIFICATION_COOLDOWN:
                intruder_active = True
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                camera_location = None
                try:
                    with open('camera_location.txt', 'r') as f:
                        camera_location = f.read().strip()
                except Exception:
                    camera_location = None
                location_str = f" at your {camera_location}" if camera_location else ""
                message = f"Ã°ÂÂÂ¨ Intruder detected{location_str} at {timestamp}"
                snap_filename = f"intruder_{int(now_time)}.jpg"
                snap_filepath = os.path.join('/tmp', snap_filename)
                cv2.imwrite(snap_filepath, frame)
                try:
                    with open(snap_filepath, 'rb') as f:
                        bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=f, caption=message)
                except Exception as e:
                    print(f"[ERROR] Failed to send photo to Telegram: {e}")
                last_notification_time['intruder'] = now_time
            # Keep beeping as long as unknown is present
            if now - last_beep_time > 1.0:
                threading.Thread(target=beep, args=(1, 0.2)).start()
                last_beep_time = now
            currentname = "Unknown"
            intruder_last_seen = now
            # Log unknown detection event
            log_detection_event('unknown', now - (recording_start_time or now), {})
        elif any(n != "Unknown" for n in names):
            # Check if we should notify about known person
            for name in names:
                if name != "Unknown":
                    current_time = time.time()
                    if (name not in last_notification_time or
                        current_time - last_notification_time[name] > NOTIFICATION_COOLDOWN):
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        camera_location = None
                        try:
                            with open('camera_location.txt', 'r') as f:
                                camera_location = f.read().strip()
                        except Exception:
                            camera_location = None
                        location_str = f" at your {camera_location}" if camera_location else ""
                        message = f"Ã°ÂÂÂ {name} detected{location_str} at {timestamp}"
                        send_telegram_notification(message)
                        last_notification_time[name] = current_time
                        log_detection_event('known', now - (recording_start_time or now), {'name': name})
            currentname = name
            intruder_active = False
    # If no unknown detected for 3 seconds, reset intruder state
    if intruder_active and now - intruder_last_seen > 3:
        intruder_active = False

    return frame

def gen_frames():
    global recording, recording_writer, recording_folder, recording_filename, recording_pending, pending_recording_info, last_frame_size, recording_start_time, recording_frame_count
    while True:
        frame = vs.read()
        frame = imutils.resize(frame, width=500)
        frame = recognize_and_draw(frame)
        # Update last_frame_size
        last_frame_size = (frame.shape[1], frame.shape[0])
        # Handle pending recording
        with recording_lock:
            if recording_pending:
                folder_name = pending_recording_info['folder_name']
                filename = pending_recording_info['filename']
                folder_path = os.path.join(VIDEO_DIR, folder_name)
                os.makedirs(folder_path, exist_ok=True)
                file_path = os.path.join(folder_path, filename)
                fourcc = cv2.VideoWriter_fourcc(*'MJPG')
                # Set FPS to 10.0 for initial recording (will fix with ffmpeg later)
                recording_writer = cv2.VideoWriter(file_path, fourcc, 10.0, last_frame_size)
                if not recording_writer.isOpened():
                    print("[ERROR] Failed to open video writer (dynamic size)")
                    recording_writer = None
                else:
                    recording = True
                    recording_folder = folder_name
                    recording_filename = filename
                    recording_start_time = time.time()
                    recording_frame_count = 0
                    print(f"[DEBUG] Started recording (dynamic): folder={folder_name}, file={filename}, size={last_frame_size}")
                recording_pending = False
                pending_recording_info = {}
            if recording and recording_writer is not None:
                try:
                    recording_writer.write(frame)
                    recording_frame_count += 1
                except Exception as e:
                    print(f"[ERROR] Failed to write frame: {e}")
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video')
def video():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def handle_telegram_commands():
    updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    def enable_motionsense_cmd(update, context):
        with app.test_client() as client:
            client.post('/set-motion-sensor', json={'enabled': True})
        update.message.reply_text("Ã¢ÂÂ Motion sensor enabled")

    def disable_motionsense_cmd(update, context):
        with app.test_client() as client:
            client.post('/set-motion-sensor', json={'enabled': False})
        update.message.reply_text("Ã¢ÂÂ Motion sensor disabled")

    def enable_sounds_cmd(update, context):
        with app.test_client() as client:
            client.post('/set-buzzer', json={'enabled': True})
        update.message.reply_text("Ã°ÂÂÂ Sounds enabled")

    def disable_sounds_cmd(update, context):
        with app.test_client() as client:
            client.post('/set-buzzer', json={'enabled': False})
        update.message.reply_text("Ã°ÂÂÂ Sounds disabled")

    def enable_servo_cmd(update, context):
        with app.test_client() as client:
            client.post('/set-servo', json={'enabled': True})
        update.message.reply_text("Ã°ÂÂÂ Servo enabled")

    def disable_servo_cmd(update, context):
        with app.test_client() as client:
            client.post('/set-servo', json={'enabled': False})
        update.message.reply_text("Ã¢ÂÂ¹ Servo disabled")

    def enable_led_cmd(update, context):
        with app.test_client() as client:
            client.post('/set-led', json={'enabled': True})
        update.message.reply_text("Ã°ÂÂÂ¡ LED enabled")

    def disable_led_cmd(update, context):
        with app.test_client() as client:
            client.post('/set-led', json={'enabled': False})
        update.message.reply_text("Ã°ÂÂÂ LED disabled")

    def set_servo_angle_cmd(update, context):
        try:
            angle = int(context.args[0])
            if not (0 <= angle <= 180):
                update.message.reply_text("Ã¢ÂÂ Angle must be between 0 and 180.")
                return
        except (IndexError, ValueError):
            update.message.reply_text("Usage: /servo_angle <0-180>")
            return
        with app.test_client() as client:
            resp = client.post('/set-servo-angle', json={'angle': angle})
            if resp.status_code == 200:
                update.message.reply_text(f"Ã°ÂÂÂ Servo moved to {angle}ÃÂ°")
            else:
                update.message.reply_text("Ã¢ÂÂ Failed to move servo.")

    def snap_cmd(update, context):
        with app.test_client() as client:
            resp = client.post('/snap')
            if resp.status_code == 200:
                data = resp.get_json()
                filepath = data.get('filepath')
                if filepath and os.path.exists(filepath):
                    with open(filepath, 'rb') as f:
                        update.message.reply_photo(f)
                else:
                    update.message.reply_text("Ã¢ÂÂ Failed to take snapshot.")
            else:
                update.message.reply_text("Ã¢ÂÂ Failed to take snapshot.")

    def status_cmd(update, context):
        status_msg = f"""
Ã°ÂÂÂ System Status:
- Motion Sensor: {'Ã¢ÂÂ' if motion_sensor_enabled else 'Ã¢ÂÂ'}
- Sounds: {'Ã°ÂÂÂ' if buzzer_enabled else 'Ã°ÂÂÂ'}
- Servo: {'Ã°ÂÂÂ' if servo_enabled else 'Ã¢ÂÂ¹'}
- LED: {'Ã°ÂÂÂ¡' if led_enabled else 'Ã°ÂÂÂ'}
"""
        update.message.reply_text(status_msg)

    def help_cmd(update, context):
        help_msg = """
Ã°ÂÂ¤Â Available Commands:
/enable_motion - Enable motion sensor
/disable_motion - Disable motion sensor
/enable_sound - Enable sounds
/disable_sound - Disable sounds
/enable_servo - Enable servo
/disable_servo - Disable servo
/enable_led - Enable LED
/disable_led - Disable LED
/servo_angle <0-180> - Move servo to specified angle
/snap - Take a snapshot and send to Telegram
/status - Show current status
/help - Show this help message
/patrol - Start servo patrol motion
"""
        update.message.reply_text(help_msg)

    def patrol_cmd(update, context):
        def patrol_motion():
            if not HAS_GPIO or not servo_enabled:
                return
            # Sweep from left (0 deg) to right (180 deg) and back
            for angle in list(range(0, 181, 10)) + list(range(180, -1, -10)):
                servo.ChangeDutyCycle(2.5 + (angle / 180.0) * 10)
                time.sleep(0.05)
            servo.ChangeDutyCycle(0)
        update.message.reply_text("Ã°ÂÂÂ¨ Patrol started: Servo will sweep left to right.")
        def repeat_patrol():
            while True:
                patrol_motion()
                time.sleep(300)  # 5 minutes
        t = threading.Thread(target=repeat_patrol, daemon=True)
        t.start()

    # Add command handlers
    dp.add_handler(CommandHandler("enable_motion", enable_motionsense_cmd))
    dp.add_handler(CommandHandler("disable_motion", disable_motionsense_cmd))
    dp.add_handler(CommandHandler("enable_sound", enable_sounds_cmd))
    dp.add_handler(CommandHandler("disable_sound", disable_sounds_cmd))
    dp.add_handler(CommandHandler("enable_servo", enable_servo_cmd))
    dp.add_handler(CommandHandler("disable_servo", disable_servo_cmd))
    dp.add_handler(CommandHandler("enable_led", enable_led_cmd))
    dp.add_handler(CommandHandler("disable_led", disable_led_cmd))
    dp.add_handler(CommandHandler("servo_angle", set_servo_angle_cmd))
    dp.add_handler(CommandHandler("snap", snap_cmd))
    dp.add_handler(CommandHandler("status", status_cmd))
    dp.add_handler(CommandHandler("help", help_cmd))
    dp.add_handler(CommandHandler("start", help_cmd))  # /start also shows help
    dp.add_handler(CommandHandler("patrol", patrol_cmd))

    updater.start_polling()
    return updater

# Start the Telegram command handler in a separate thread
telegram_thread = threading.Thread(target=handle_telegram_commands)
telegram_thread.daemon = True
telegram_thread.start()

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5002)
    finally:
        if HAS_GPIO:
            servo.stop()
            GPIO.cleanup()



