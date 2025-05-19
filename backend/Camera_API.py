#!/usr/bin/python

#Camera_API.py
#dev by EinsbernSystems

from flask import Flask, Response, request, jsonify, send_file
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
TELEGRAM_CHAT_ID = "5304394038"
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
        self.last_move_time = time.sleep(0.1)

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

VIDEO_DIR = '/home/einsbern/facial_recognition/footage'
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
def get_recording_folder_name():
    now = datetime.now()
    return now.strftime('%B, %d, %Y - %H:%M:%S')

def get_unique_recording_folder_name():
    base_name = datetime.now().strftime('%B, %d, %Y - %H:%M:%S')
    folder_path = os.path.join(VIDEO_DIR, base_name)
    counter = 1
    unique_name = base_name
    while os.path.exists(folder_path):
        unique_name = f"{base_name} ({counter})"
        folder_path = os.path.join(VIDEO_DIR, unique_name)
        counter += 1
    return unique_name

def get_next_video_filename(folder_path):
    now = datetime.now()
    if platform.system() == 'Windows':
        filename = now.strftime('%Y-%m-%d_%H-%M-%S') + '.avi'
    else:
        filename = now.strftime('%Y-%m-%d_%H-%M-%S') + '.mov'
    return filename

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
            folder_name = req['folder_name']
            filename = req['filename']
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

def cleanup_recording():
    global recording, recording_writer
    with recording_lock:
        if recording_writer:
            recording_writer.release()
            recording_writer = None
        recording = False
atexit.register(cleanup_recording)

def recognize_and_draw(frame):
    global currentname, last_beep_time, intruder_active, intruder_last_seen, last_notification_time, last_intruder_alert

    # Convert from BGR to RGB for face_recognition
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

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
                message = f"🚨 Intruder detected{location_str} at {timestamp}"
                snap_filename = f"intruder_{int(now_time)}.jpg"
                snap_filepath = os.path.join('/tmp', snap_filename)
                cv2.imwrite(snap_filepath, frame)

                # Update last intruder alert
                last_intruder_alert = {
                    'has_alert': True,
                    'timestamp': timestamp,
                    'location': camera_location or 'Unknown location',
                    'message': message,
                    'image_url': f'/intruder-image/{snap_filename}'
                }

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
                        message = f"👋 {name} detected{location_str} at {timestamp}"
                        send_telegram_notification(message)
                        last_notification_time[name] = current_time
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
        update.message.reply_text("✅ Motion sensor enabled")

    def disable_motionsense_cmd(update, context):
        with app.test_client() as client:
            client.post('/set-motion-sensor', json={'enabled': False})
        update.message.reply_text("❌ Motion sensor disabled")

    def enable_sounds_cmd(update, context):
        with app.test_client() as client:
            client.post('/set-buzzer', json={'enabled': True})
        update.message.reply_text("🔔 Sounds enabled")

    def disable_sounds_cmd(update, context):
        with app.test_client() as client:
            client.post('/set-buzzer', json={'enabled': False})
        update.message.reply_text("🔕 Sounds disabled")

    def enable_servo_cmd(update, context):
        with app.test_client() as client:
            client.post('/set-servo', json={'enabled': True})
        update.message.reply_text("🔄 Servo enabled")

    def disable_servo_cmd(update, context):
        with app.test_client() as client:
            client.post('/set-servo', json={'enabled': False})
        update.message.reply_text("⏹ Servo disabled")

    def enable_led_cmd(update, context):
        with app.test_client() as client:
            client.post('/set-led', json={'enabled': True})
        update.message.reply_text("💡 LED enabled")

    def disable_led_cmd(update, context):
        with app.test_client() as client:
            client.post('/set-led', json={'enabled': False})
        update.message.reply_text("🌑 LED disabled")

    def set_servo_angle_cmd(update, context):
        try:
            angle = int(context.args[0])
            if not (0 <= angle <= 180):
                update.message.reply_text("❗ Angle must be between 0 and 180.")
                return
        except (IndexError, ValueError):
            update.message.reply_text("Usage: /servo_angle <0-180>")
            return
        with app.test_client() as client:
            resp = client.post('/set-servo-angle', json={'angle': angle})
            if resp.status_code == 200:
                update.message.reply_text(f"🔄 Servo moved to {angle}°")
            else:
                update.message.reply_text("❗ Failed to move servo.")

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
                    update.message.reply_text("❗ Failed to take snapshot.")
            else:
                update.message.reply_text("❗ Failed to take snapshot.")

    def status_cmd(update, context):
        status_msg = f"""
📊 System Status:
- Motion Sensor: {'✅' if motion_sensor_enabled else '❌'}
- Sounds: {'🔔' if buzzer_enabled else '🔕'}
- Servo: {'🔄' if servo_enabled else '⏹'}
- LED: {'💡' if led_enabled else '🌑'}
"""
        update.message.reply_text(status_msg)

    def help_cmd(update, context):
        help_msg = """
🤖 Available Commands:
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
        update.message.reply_text("🚨 Patrol started: Servo will sweep left to right.")
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

@app.route('/alert-interface')
def alert_interface():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Security Alert Interface</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/bootstrap-icons.css" rel="stylesheet">
        <style>
            .alert-card {
                border-radius: 15px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin-bottom: 20px;
                transition: all 0.3s ease;
            }
            .alert-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
            }
            .status-indicator {
                width: 15px;
                height: 15px;
                border-radius: 50%;
                display: inline-block;
                margin-right: 10px;
            }
            .status-active {
                background-color: #28a745;
                box-shadow: 0 0 10px #28a745;
            }
            .status-inactive {
                background-color: #dc3545;
                box-shadow: 0 0 10px #dc3545;
            }
            .servo-control {
                width: 100%;
                margin: 20px 0;
            }
            .intruder-image {
                max-width: 100%;
                border-radius: 10px;
                margin-top: 10px;
            }
            .notification {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 1000;
                animation: slideIn 0.5s ease-out;
            }
            @keyframes slideIn {
                from { transform: translateX(100%); }
                to { transform: translateX(0); }
            }
            .control-panel {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 15px;
                margin-bottom: 20px;
            }
            .btn-control {
                margin: 5px;
                min-width: 120px;
            }
            .video-container {
                position: relative;
                width: 100%;
                border-radius: 10px;
                overflow: hidden;
            }
            .video-feed {
                width: 100%;
                border-radius: 10px;
            }
            .alert-history {
                max-height: 300px;
                overflow-y: auto;
            }
            .alert-item {
                padding: 10px;
                border-left: 4px solid #dc3545;
                margin-bottom: 10px;
                background: #fff;
                border-radius: 0 10px 10px 0;
            }
            .health-indicator {
                padding: 10px;
                border-radius: 10px;
                margin-bottom: 10px;
            }
            .quick-action {
                text-align: center;
                padding: 15px;
                border-radius: 10px;
                background: #f8f9fa;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            .quick-action:hover {
                background: #e9ecef;
                transform: scale(1.05);
            }
            .quick-action i {
                font-size: 24px;
                margin-bottom: 10px;
            }
            .network-status {
                padding: 15px;
                border-radius: 10px;
                background: #f8f9fa;
                margin-bottom: 10px;
            }
            .recording-item {
                padding: 10px;
                border-left: 4px solid #0d6efd;
                margin-bottom: 10px;
                background: #fff;
                border-radius: 0 10px 10px 0;
            }
            .log-entry {
                font-family: monospace;
                padding: 5px;
                border-bottom: 1px solid #dee2e6;
            }
            .face-training {
                padding: 20px;
                border-radius: 10px;
                background: #f8f9fa;
            }
            .recording-actions {
                display: flex;
                gap: 10px;
                margin-top: 5px;
            }
            .face-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px;
                background: #fff;
                border-radius: 10px;
                margin-bottom: 10px;
            }
            .face-count {
                background: #e9ecef;
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 0.9em;
            }
            .delete-btn {
                color: #dc3545;
                cursor: pointer;
            }
            .delete-btn:hover {
                color: #bd2130;
            }
        </style>
    </head>
    <body class="bg-light">
        <div class="container py-4">
            <h1 class="text-center mb-4">Security Alert Interface</h1>

            <!-- Quick Actions Panel -->
            <div class="row mb-4">
                <div class="col-12">
                    <div class="alert-card card">
                        <div class="card-body">
                            <h5 class="card-title">Quick Actions</h5>
                            <div class="row">
                                <div class="col-md-3">
                                    <div class="quick-action" onclick="takeSnapshot()">
                                        <i class="bi bi-camera"></i>
                                        <div>Take Snapshot</div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="quick-action" onclick="togglePatrol()">
                                        <i class="bi bi-shield-check"></i>
                                        <div>Toggle Patrol</div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="quick-action" onclick="toggleRecording()">
                                        <i class="bi bi-record-circle"></i>
                                        <div>Toggle Recording</div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="quick-action" onclick="showSystemStatus()">
                                        <i class="bi bi-info-circle"></i>
                                        <div>System Status</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Main Control Panels -->
            <div class="row mb-4">
                <div class="col-md-6">
                    <div class="alert-card card">
                        <div class="card-body">
                            <h5 class="card-title">Live Video Feed</h5>
                            <div class="video-container">
                                <img src="/video" class="video-feed" alt="Live Feed">
                            </div>
                        </div>
                    </div>
                </div>

                <div class="col-md-6">
                    <div class="alert-card card">
                        <div class="card-body">
                            <h5 class="card-title">System Health</h5>
                            <div id="health-container">
                                <div class="health-indicator">
                                    <div class="d-flex justify-content-between">
                                        <span>CPU Usage</span>
                                        <span id="cpu-usage">--</span>
                                    </div>
                                    <div class="progress">
                                        <div id="cpu-bar" class="progress-bar" role="progressbar" style="width: 0%"></div>
                                    </div>
                                </div>
                                <div class="health-indicator">
                                    <div class="d-flex justify-content-between">
                                        <span>Memory Usage</span>
                                        <span id="memory-usage">--</span>
                                    </div>
                                    <div class="progress">
                                        <div id="memory-bar" class="progress-bar" role="progressbar" style="width: 0%"></div>
                                    </div>
                                </div>
                                <div class="health-indicator">
                                    <div class="d-flex justify-content-between">
                                        <span>Disk Space</span>
                                        <span id="disk-usage">--</span>
                                    </div>
                                    <div class="progress">
                                        <div id="disk-bar" class="progress-bar" role="progressbar" style="width: 0%"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Status and Control Panels -->
            <div class="row mb-4">
                <div class="col-md-6">
                    <div class="alert-card card">
                        <div class="card-body">
                            <h5 class="card-title">System Status</h5>
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <span class="status-indicator" id="motion-status"></span>
                                    Motion Sensor
                                </div>
                                <div class="form-check form-switch">
                                    <input class="form-check-input" type="checkbox" id="motion-toggle">
                                </div>
                            </div>
                            <div class="d-flex justify-content-between align-items-center mt-2">
                                <div>
                                    <span class="status-indicator" id="sound-status"></span>
                                    Sound Alerts
                                </div>
                                <div class="form-check form-switch">
                                    <input class="form-check-input" type="checkbox" id="sound-toggle">
                                </div>
                            </div>
                            <div class="d-flex justify-content-between align-items-center mt-2">
                                <div>
                                    <span class="status-indicator" id="led-status"></span>
                                    LED Indicator
                                </div>
                                <div class="form-check form-switch">
                                    <input class="form-check-input" type="checkbox" id="led-toggle">
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="col-md-6">
                    <div class="alert-card card">
                        <div class="card-body">
                            <h5 class="card-title">Servo Control</h5>
                            <div class="servo-control">
                                <input type="range" class="form-range" id="servo-slider" min="0" max="180" value="90">
                                <div class="text-center mt-2">
                                    <span id="servo-value">90°</span>
                                </div>
                            </div>
                            <div class="d-flex justify-content-center mt-3">
                                <button class="btn btn-primary btn-control" id="patrol-btn">Start Patrol</button>
                                <button class="btn btn-danger btn-control" id="stop-patrol-btn">Stop Patrol</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Alert History Panel -->
            <div class="row">
                <div class="col-12">
                    <div class="alert-card card">
                        <div class="card-body">
                            <h5 class="card-title">Alert History</h5>
                            <div class="alert-history" id="alert-history">
                                <!-- Alert items will be added here dynamically -->
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Network Status Panel -->
            <div class="row mb-4">
                <div class="col-12">
                    <div class="alert-card card">
                        <div class="card-body">
                            <h5 class="card-title">Network Status</h5>
                            <div id="network-status">
                                <div class="network-status">
                                    <div class="d-flex justify-content-between">
                                        <span>WiFi Network:</span>
                                        <span id="wifi-ssid">--</span>
                                    </div>
                                </div>
                                <div class="network-status">
                                    <div class="d-flex justify-content-between">
                                        <span>IP Address:</span>
                                        <span id="ip-address">--</span>
                                    </div>
                                </div>
                                <div class="network-status">
                                    <div class="d-flex justify-content-between">
                                        <span>Signal Strength:</span>
                                        <span id="signal-strength">--</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Recording History Panel with Actions -->
            <div class="row mb-4">
                <div class="col-12">
                    <div class="alert-card card">
                        <div class="card-body">
                            <h5 class="card-title">Recording History</h5>
                            <div id="recording-history">
                                <!-- Recording items will be added here dynamically -->
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Trained Faces Management Panel -->
            <div class="row mb-4">
                <div class="col-12">
                    <div class="alert-card card">
                        <div class="card-body">
                            <h5 class="card-title">Trained Faces</h5>
                            <div id="trained-faces">
                                <!-- Face items will be added here dynamically -->
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Face Training Panel -->
            <div class="row mb-4">
                <div class="col-12">
                    <div class="alert-card card">
                        <div class="card-body">
                            <h5 class="card-title">Face Recognition Training</h5>
                            <div class="face-training">
                                <form id="face-training-form" class="mb-3">
                                    <div class="mb-3">
                                        <label for="name" class="form-label">Person's Name</label>
                                        <input type="text" class="form-control" id="name" required>
                                    </div>
                                    <div class="mb-3">
                                        <label for="face-image" class="form-label">Face Image</label>
                                        <input type="file" class="form-control" id="face-image" accept="image/*" required>
                                    </div>
                                    <button type="submit" class="btn btn-primary">Train Face</button>
                                </form>
                                <div id="training-result"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- System Logs Panel -->
            <div class="row">
                <div class="col-12">
                    <div class="alert-card card">
                        <div class="card-body">
                            <h5 class="card-title">System Logs</h5>
                            <div id="system-logs" class="bg-dark text-light p-3" style="max-height: 300px; overflow-y: auto;">
                                <!-- Log entries will be added here dynamically -->
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            // Status indicators
            function updateStatus(elementId, isActive) {
                const indicator = document.getElementById(elementId);
                indicator.className = 'status-indicator ' + (isActive ? 'status-active' : 'status-inactive');
            }

            // Initialize status
            function initializeStatus() {
                fetch('/status')
                    .then(response => response.json())
                    .then(data => {
                        updateStatus('motion-status', data.motion_sensor_enabled);
                        updateStatus('sound-status', data.buzzer_enabled);
                        updateStatus('led-status', data.led_enabled);

                        document.getElementById('motion-toggle').checked = data.motion_sensor_enabled;
                        document.getElementById('sound-toggle').checked = data.buzzer_enabled;
                        document.getElementById('led-toggle').checked = data.led_enabled;
                    });
            }

            // Servo control
            const servoSlider = document.getElementById('servo-slider');
            const servoValue = document.getElementById('servo-value');

            servoSlider.addEventListener('input', function() {
                servoValue.textContent = this.value + '°';
            });

            servoSlider.addEventListener('change', function() {
                fetch('/set-servo-angle', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ angle: parseInt(this.value) })
                });
            });

            // Toggle controls
            document.getElementById('motion-toggle').addEventListener('change', function() {
                fetch('/set-motion-sensor', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ enabled: this.checked })
                }).then(() => updateStatus('motion-status', this.checked));
            });

            document.getElementById('sound-toggle').addEventListener('change', function() {
                fetch('/set-buzzer', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ enabled: this.checked })
                }).then(() => updateStatus('sound-status', this.checked));
            });

            document.getElementById('led-toggle').addEventListener('change', function() {
                fetch('/set-led', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ enabled: this.checked })
                }).then(() => updateStatus('led-status', this.checked));
            });

            // Patrol controls
            document.getElementById('patrol-btn').addEventListener('click', function() {
                fetch('/patrol', { method: 'POST' });
            });

            document.getElementById('stop-patrol-btn').addEventListener('click', function() {
                fetch('/stop-patrol', { method: 'POST' });
            });

            // New functions for enhanced features
            function takeSnapshot() {
                fetch('/snap', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            showNotification('📸 Snapshot', 'Snapshot taken successfully');
                        }
                    });
            }

            function togglePatrol() {
                const patrolBtn = document.getElementById('patrol-btn');
                if (patrolBtn.textContent === 'Start Patrol') {
                    fetch('/patrol', { method: 'POST' });
                    patrolBtn.textContent = 'Stop Patrol';
                } else {
                    fetch('/stop-patrol', { method: 'POST' });
                    patrolBtn.textContent = 'Start Patrol';
                }
            }

            function toggleRecording() {
                fetch('/toggle-recording', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        showNotification('🎥 Recording', data.message);
                    });
            }

            function showSystemStatus() {
                fetch('/system-status')
                    .then(response => response.json())
                    .then(data => {
                        updateHealthIndicators(data);
                    });
            }

            function updateHealthIndicators(data) {
                document.getElementById('cpu-usage').textContent = data.cpu + '%';
                document.getElementById('cpu-bar').style.width = data.cpu + '%';
                document.getElementById('memory-usage').textContent = data.memory + '%';
                document.getElementById('memory-bar').style.width = data.memory + '%';
                document.getElementById('disk-usage').textContent = data.disk + '%';
                document.getElementById('disk-bar').style.width = data.disk + '%';
            }

            function addAlertToHistory(alert) {
                const history = document.getElementById('alert-history');
                const alertItem = document.createElement('div');
                alertItem.className = 'alert-item';
                alertItem.innerHTML = `
                    <div class="d-flex justify-content-between">
                        <strong>${alert.type}</strong>
                        <small>${alert.time}</small>
                    </div>
                    <div>${alert.message}</div>
                `;
                history.insertBefore(alertItem, history.firstChild);
            }

            // Enhanced intruder alert handling
            function checkIntruderAlerts() {
                fetch('/intruder-alert')
                    .then(response => response.json())
                    .then(data => {
                        if (data.has_alert) {
                            document.getElementById('no-intruder-message').classList.add('d-none');
                            document.getElementById('intruder-image').classList.remove('d-none');
                            document.getElementById('intruder-details').classList.remove('d-none');

                            document.getElementById('intruder-image').src = data.image_url;
                            document.getElementById('intruder-time').textContent = data.timestamp;
                            document.getElementById('intruder-location').textContent = data.location;

                            // Add to history
                            addAlertToHistory({
                                type: '🚨 Intruder Alert',
                                time: data.timestamp,
                                message: data.message
                            });

                            // Show notification
                            showNotification('🚨 Intruder Alert!', data.message);
                        }
                    });
            }

            // Network status monitoring
            function updateNetworkStatus() {
                fetch('/network-status')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('wifi-ssid').textContent = data.ssid;
                        document.getElementById('ip-address').textContent = data.ip;
                        document.getElementById('signal-strength').textContent = data.signal;
                    });
            }

            // Enhanced recording history with actions
            function updateRecordingHistory() {
                fetch('/recording-history')
                    .then(response => response.json())
                    .then(data => {
                        const history = document.getElementById('recording-history');
                        history.innerHTML = '';
                        data.forEach(recording => {
                            const item = document.createElement('div');
                            item.className = 'recording-item';
                            const filename = `${recording.folder}/${recording.filename}`;
                            item.innerHTML = `
                                <div class="d-flex justify-content-between">
                                    <strong>${recording.folder}</strong>
                                    <small>${recording.created}</small>
                                </div>
                                <div>${recording.filename} (${(recording.size / 1024 / 1024).toFixed(2)} MB)</div>
                                <div class="recording-actions">
                                    <button class="btn btn-sm btn-primary" onclick="downloadRecording('${filename}')">
                                        <i class="bi bi-download"></i> Download
                                    </button>
                                    <button class="btn btn-sm btn-danger" onclick="deleteRecording('${filename}')">
                                        <i class="bi bi-trash"></i> Delete
                                    </button>
                                </div>
                            `;
                            history.appendChild(item);
                        });
                    });
            }

            // Download recording
            function downloadRecording(filename) {
                window.location.href = `/download-recording/${filename}`;
            }

            // Delete recording
            function deleteRecording(filename) {
                if (confirm('Are you sure you want to delete this recording?')) {
                    fetch(`/delete-recording/${filename}`, {
                        method: 'DELETE'
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            updateRecordingHistory();
                            showNotification('🗑️ Recording Deleted', 'Recording has been deleted successfully');
                        } else {
                            showNotification('❌ Error', data.error || 'Failed to delete recording');
                        }
                    });
                }
            }

            // Update trained faces list
            function updateTrainedFaces() {
                fetch('/trained-faces')
                    .then(response => response.json())
                    .then(data => {
                        const container = document.getElementById('trained-faces');
                        container.innerHTML = '';
                        Object.entries(data).forEach(([name, count]) => {
                            const item = document.createElement('div');
                            item.className = 'face-item';
                            item.innerHTML = `
                                <div>
                                    <strong>${name}</strong>
                                    <span class="face-count">${count} faces</span>
                                </div>
                                <i class="bi bi-trash delete-btn" onclick="deleteFace('${name}')"></i>
                            `;
                            container.appendChild(item);
                        });
                    });
            }

            // Delete trained face
            function deleteFace(name) {
                if (confirm(`Are you sure you want to delete all trained faces for ${name}?`)) {
                    fetch(`/delete-face/${name}`, {
                        method: 'DELETE'
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            updateTrainedFaces();
                            showNotification('🗑️ Face Deleted', `All trained faces for ${name} have been deleted`);
                        } else {
                            showNotification('❌ Error', data.error || 'Failed to delete face');
                        }
                    });
                }
            }

            // Face training
            document.getElementById('face-training-form').addEventListener('submit', function(e) {
                e.preventDefault();
                const formData = new FormData();
                formData.append('name', document.getElementById('name').value);
                formData.append('image', document.getElementById('face-image').files[0]);

                fetch('/train-face', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    const result = document.getElementById('training-result');
                    if (data.error) {
                        result.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                    } else {
                        result.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
                    }
                });
            });

            // System logs
            function updateSystemLogs() {
                fetch('/system-logs')
                    .then(response => response.json())
                    .then(data => {
                        const logs = document.getElementById('system-logs');
                        logs.innerHTML = '';
                        data.logs.forEach(log => {
                            const entry = document.createElement('div');
                            entry.className = 'log-entry';
                            entry.textContent = log;
                            logs.appendChild(entry);
                        });
                        logs.scrollTop = logs.scrollHeight;
                    });
            }

            // Initialize and start periodic updates
            initializeStatus();
            checkIntruderAlerts();
            updateNetworkStatus();
            updateRecordingHistory();
            updateTrainedFaces();
            updateSystemLogs();
            setInterval(checkIntruderAlerts, 5000);
            setInterval(updateNetworkStatus, 30000);
            setInterval(updateRecordingHistory, 60000);
            setInterval(updateTrainedFaces, 30000);
            setInterval(updateSystemLogs, 10000);
        </script>
    </body>
    </html>
    """

@app.route('/status')
def get_status():
    return jsonify({
        'motion_sensor_enabled': motion_sensor_enabled,
        'buzzer_enabled': buzzer_enabled,
        'led_enabled': led_enabled,
        'servo_enabled': servo_enabled
    })

@app.route('/intruder-alert')
def get_intruder_alert():
    global last_intruder_alert
    if last_intruder_alert:
        return jsonify(last_intruder_alert)
    return jsonify({'has_alert': False})

# Add to global variables at the top
last_intruder_alert = None

@app.route('/intruder-image/<filename>')
def serve_intruder_image(filename):
    return send_file(f'/tmp/{filename}', mimetype='image/jpeg')

@app.route('/system-status')
def get_system_status():
    try:
        import psutil
        return jsonify({
            'cpu': round(psutil.cpu_percent()),
            'memory': round(psutil.virtual_memory().percent),
            'disk': round(psutil.disk_usage('/').percent)
        })
    except Exception as e:
        return jsonify({
            'cpu': 0,
            'memory': 0,
            'disk': 0,
            'error': str(e)
        })

@app.route('/toggle-recording', methods=['POST'])
def toggle_recording():
    global recording
    if recording:
        return stop_recording()
    else:
        return start_recording()

@app.route('/network-status')
def get_network_status():
    try:
        # Get WiFi SSID
        ssid = subprocess.check_output(['iwconfig', 'wlan0']).decode('utf-8')
        ssid = ssid.split('ESSID:"')[1].split('"')[0] if 'ESSID:"' in ssid else 'Not Connected'

        # Get IP address
        ip = subprocess.check_output(['hostname', '-I']).decode('utf-8').split()[0]

        # Get signal strength
        signal = subprocess.check_output(['iwconfig', 'wlan0']).decode('utf-8')
        signal = signal.split('Signal level=')[1].split()[0] if 'Signal level=' in signal else 'Unknown'

        return jsonify({
            'ssid': ssid,
            'ip': ip,
            'signal': signal,
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

@app.route('/recording-history')
def get_recording_history():
    try:
        recordings = []
        for folder in os.listdir(VIDEO_DIR):
            folder_path = os.path.join(VIDEO_DIR, folder)
            if os.path.isdir(folder_path):
                for file in os.listdir(folder_path):
                    if file.endswith('.mp4'):
                        file_path = os.path.join(folder_path, file)
                        recordings.append({
                            'folder': folder,
                            'filename': file,
                            'size': os.path.getsize(file_path),
                            'created': datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
                        })
        return jsonify(sorted(recordings, key=lambda x: x['created'], reverse=True))
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/system-logs')
def get_system_logs():
    try:
        logs = []
        # Get last 100 lines of system log
        with open('/var/log/syslog', 'r') as f:
            logs = f.readlines()[-100:]
        return jsonify({'logs': logs})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/train-face', methods=['POST'])
def train_face():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400

        image = request.files['image']
        name = request.form.get('name', 'Unknown')

        # Save image temporarily
        temp_path = f'/tmp/train_{int(time.time())}.jpg'
        image.save(temp_path)

        # Process image with face_recognition
        image = face_recognition.load_image_file(temp_path)
        encodings = face_recognition.face_encodings(image)

        if not encodings:
            return jsonify({'error': 'No face detected in image'}), 400

        # Update encodings.pickle
        data = pickle.loads(open(encodingsP, "rb").read())
        data["encodings"].append(encodings[0])
        data["names"].append(name)

        with open(encodingsP, "wb") as f:
            f.write(pickle.dumps(data))

        os.remove(temp_path)
        return jsonify({'success': True, 'message': f'Face trained for {name}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download-recording/<path:filename>')
def download_recording(filename):
    try:
        folder, file = filename.split('/')
        file_path = os.path.join(VIDEO_DIR, folder, file)
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/delete-recording/<path:filename>', methods=['DELETE'])
def delete_recording(filename):
    try:
        folder, file = filename.split('/')
        file_path = os.path.join(VIDEO_DIR, folder, file)
        os.remove(file_path)
        # If folder is empty, remove it too
        folder_path = os.path.join(VIDEO_DIR, folder)
        if not os.listdir(folder_path):
            os.rmdir(folder_path)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/trained-faces')
def get_trained_faces():
    try:
        data = pickle.loads(open(encodingsP, "rb").read())
        # Count occurrences of each name
        face_counts = {}
        for name in data["names"]:
            face_counts[name] = face_counts.get(name, 0) + 1
        return jsonify(face_counts)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete-face/<name>', methods=['DELETE'])
def delete_face(name):
    try:
        data = pickle.loads(open(encodingsP, "rb").read())
        # Find all indices for this name
        indices = [i for i, n in enumerate(data["names"]) if n == name]
        # Remove entries in reverse order to avoid index issues
        for i in sorted(indices, reverse=True):
            del data["encodings"][i]
            del data["names"][i]
        # Save updated data
        with open(encodingsP, "wb") as f:
            f.write(pickle.dumps(data))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5002)
    finally:
        if HAS_GPIO:
            servo.stop()
            GPIO.cleanup()
