from flask import Flask, send_from_directory, jsonify, request, send_file, Response
from flask_cors import CORS
import os
import time
import shutil
import subprocess
import mimetypes
import re
import datetime

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

KNOWN_FACES_DIR = '/home/einsbern/facial_recognition/dataset'
VIDEO_DIR = '/home/einsbern/facial_recognition/footage'
VENV_PYTHON = '/home/einsbern/camenv/bin/python'
TRAIN_SCRIPT = '/home/einsbern/facial_recognition/train_model.py'
TRAIN_CWD = '/home/einsbern/facial_recognition'

def parse_date_from_folder_name(name):
    # Example: 'May, 07, 2025 - 14:23:45'
    try:
        return datetime.datetime.strptime(name, '%B, %d, %Y - %H:%M:%S')
    except Exception:
        return None

def parse_date_from_video_filename(name):
    # Example: '2025-05-07_14-23-45.mp4'
    import re
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})-(\d{2})', name)
    if m:
        try:
            return datetime.datetime.strptime('_'.join(m.groups()), '%Y_%m_%d_%H_%M_%S')
        except Exception:
            return None
    return None

@app.route('/api/images')
def list_images():
    files = [f for f in os.listdir(KNOWN_FACES_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    return jsonify(files)

@app.route('/known_faces/<filename>')
def serve_image(filename):
    return send_from_directory(KNOWN_FACES_DIR, filename, as_attachment=False)

@app.route('/api/upload', methods=['POST'])
def upload_images():
    folder = request.form.get('folder')
    if not folder:
        return jsonify({"error": "No folder specified"}), 400

    target_folder = os.path.join(KNOWN_FACES_DIR, folder)
    os.makedirs(target_folder, exist_ok=True)

    if 'images' not in request.files:
        return jsonify({"error": "No files part"}), 400

    files = request.files.getlist('images')
    saved = []

    for file in files:
        if file and file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            save_path = os.path.join(target_folder, file.filename)
            file.save(save_path)
            saved.append(file.filename)

    return jsonify({"uploaded": saved}), 200

@app.route('/api/upload-video', methods=['POST'])
def upload_videos():
    folder = request.form.get('folder')
    if not folder:
        return jsonify({"error": "No folder specified"}), 400

    target_folder = os.path.join(VIDEO_DIR, folder)
    os.makedirs(target_folder, exist_ok=True)

    if 'videos' not in request.files:
        return jsonify({"error": "No files part"}), 400

    files = request.files.getlist('videos')
    saved = []

    for file in files:
        if file and file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            save_path = os.path.join(target_folder, file.filename)
            file.save(save_path)
            saved.append(file.filename)

    return jsonify({"uploaded": saved}), 200

@app.route('/api/folders')
def list_folders():
    folders = [entry.name for entry in os.scandir(VIDEO_DIR) if entry.is_dir()]
    return jsonify(folders)

@app.route('/api/folder-images')
def list_folder_images():
    folder = request.args.get('folder')
    if not folder:
        return jsonify({'error': 'No folder specified'}), 400
    folder_path = os.path.join(KNOWN_FACES_DIR, folder)
    if not os.path.isdir(folder_path):
        return jsonify({'error': 'Folder not found'}), 404
    images = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    return jsonify(images)

@app.route('/api/folder-videos')
def list_folder_videos():
    folder = request.args.get('folder')
    if not folder:
        return jsonify({'error': 'No folder specified'}), 400
    folder_path = os.path.join(VIDEO_DIR, folder)
    if not os.path.isdir(folder_path):
        return jsonify({'error': 'Folder not found'}), 404
    videos = [f for f in os.listdir(folder_path) if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))]
    def sort_key(name):
        dt = parse_date_from_video_filename(name)
        return (dt or datetime.datetime.min, name)
    videos.sort(key=sort_key)
    return jsonify(videos)

@app.route('/api/image-folders')
def list_image_folders():
    folders = [entry.name for entry in os.scandir(KNOWN_FACES_DIR) if entry.is_dir()]
    return jsonify(folders)

@app.route('/api/video-folders')
def list_video_folders():
    folders = [entry.name for entry in os.scandir(VIDEO_DIR) if entry.is_dir()]
    def sort_key(name):
        dt = parse_date_from_folder_name(name)
        return (dt or datetime.datetime.min, name)
    folders.sort(key=sort_key)
    return jsonify(folders)

@app.route('/dataset/<folder>/<filename>')
def serve_folder_image(folder, filename):
    folder_path = os.path.join(KNOWN_FACES_DIR, folder)
    return send_from_directory(folder_path, filename, as_attachment=False)

@app.route('/footage/<folder>/<filename>')
def serve_video(folder, filename):
    folder_path = os.path.join(VIDEO_DIR, folder)
    file_path = os.path.join(folder_path, filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404

    range_header = request.headers.get('Range', None)
    if not range_header:
        return send_file(file_path, mimetype=mimetypes.guess_type(file_path)[0] or 'application/octet-stream')

    size = os.path.getsize(file_path)
    byte1, byte2 = 0, None
    m = re.search(r'bytes=(\d+)-(\d*)', range_header)
    if m:
        g = m.groups()
        byte1 = int(g[0])
        if g[1]:
            byte2 = int(g[1])
    length = size - byte1 if byte2 is None else byte2 - byte1 + 1

    with open(file_path, 'rb') as f:
        f.seek(byte1)
        data = f.read(length)

    rv = Response(data, 206, mimetype=mimetypes.guess_type(file_path)[0] or 'application/octet-stream', direct_passthrough=True)
    rv.headers.add('Content-Range', f'bytes {byte1}-{byte1 + length - 1}/{size}')
    rv.headers.add('Accept-Ranges', 'bytes')
    rv.headers.add('Content-Length', str(length))
    return rv

@app.route('/api/rename-folder', methods=['POST'])
def rename_folder():
    data = request.json
    folder_type = data.get('type')
    old_name = data.get('oldName')
    new_name = data.get('newName')
    if not old_name or not new_name:
        return jsonify({'error': 'Missing folder name(s)'}), 400

    base_dir = KNOWN_FACES_DIR if folder_type == 'image' else VIDEO_DIR
    old_path = os.path.join(base_dir, old_name)
    new_path = os.path.join(base_dir, new_name)

    if not os.path.exists(old_path):
        return jsonify({'error': 'Folder does not exist'}), 404
    if os.path.exists(new_path):
        return jsonify({'error': 'New folder name already exists'}), 409

    os.rename(old_path, new_path)
    return jsonify({'success': True})

@app.route('/api/delete-folder', methods=['POST'])
def delete_folder():
    data = request.json
    folder_type = data.get('type')
    folder_name = data.get('name')
    if not folder_name:
        return jsonify({'error': 'Missing folder name'}), 400

    base_dir = KNOWN_FACES_DIR if folder_type == 'image' else VIDEO_DIR
    folder_path = os.path.join(base_dir, folder_name)
    if not os.path.exists(folder_path):
        return jsonify({'error': 'Folder does not exist'}), 404

    shutil.rmtree(folder_path)
    return jsonify({'success': True})

@app.route('/api/download-folder', methods=['GET'])
def download_folder():
    folder_type = request.args.get('type')
    folder_name = request.args.get('name')
    if not folder_name:
        return jsonify({'error': 'Missing folder name'}), 400

    base_dir = KNOWN_FACES_DIR if folder_type == 'image' else VIDEO_DIR
    folder_path = os.path.join(base_dir, folder_name)
    if not os.path.exists(folder_path):
        return jsonify({'error': 'Folder does not exist'}), 404

    zip_path = f"/tmp/{folder_name}.zip"
    shutil.make_archive(f"/tmp/{folder_name}", 'zip', folder_path)
    return send_file(zip_path, as_attachment=True)

@app.route('/api/create-folder', methods=['POST'])
def create_folder():
    data = request.json
    folder = data.get('name') or data.get('folder')
    if not folder:
        return jsonify({'error': 'No folder specified'}), 400

    target_folder = os.path.join(KNOWN_FACES_DIR, folder)
    if os.path.exists(target_folder):
        return jsonify({'error': 'Folder already exists'}), 409

    os.makedirs(target_folder, exist_ok=True)
    return jsonify({'created': folder}), 201

@app.route('/api/train-model', methods=['POST'])
def train_model():
    try:
        if not os.path.isfile(VENV_PYTHON):
            return jsonify({'error': f'Python interpreter not found at {VENV_PYTHON}'}), 500
        if not os.path.isfile(TRAIN_SCRIPT):
            return jsonify({'error': f'train_model.py not found at {TRAIN_SCRIPT}'}), 500
        process = subprocess.Popen(
            [VENV_PYTHON, TRAIN_SCRIPT],
            cwd=TRAIN_CWD,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate(timeout=10)
        if process.returncode != 0:
            return jsonify({'error': f'train_model.py failed: {stderr.decode()}'}), 500
        return jsonify({'status': 'started', 'output': stdout.decode()}), 202
    except subprocess.TimeoutExpired:
        return jsonify({'status': 'started (background)'}), 202
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500

@app.route('/api/train-model-stream')
def train_model_stream():
    def generate():
        if not os.path.isfile(VENV_PYTHON):
            yield f'data: ERROR: Python interpreter not found at {VENV_PYTHON}\n\n'
            return
        if not os.path.isfile(TRAIN_SCRIPT):
            yield f'data: ERROR: train_model.py not found at {TRAIN_SCRIPT}\n\n'
            return
        process = subprocess.Popen(
            [VENV_PYTHON, TRAIN_SCRIPT],
            cwd=TRAIN_CWD,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True
        )
        try:
            for line in process.stdout:
                yield f'data: {line.rstrip()}\n\n'
            process.stdout.close()
            process.wait()
            yield f'data: [DONE]\n\n'
        except Exception as e:
            yield f'data: ERROR: {str(e)}\n\n'
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/get-logs')
def api_get_logs():
    folder = request.args.get('folder')
    video = request.args.get('video')
    print(f"[DEBUG] /api/get-logs called with folder={folder}, video={video}")
    if not (folder and video):
        return jsonify({'error': 'Missing folder or video'}), 400
    folder_path = os.path.join(VIDEO_DIR, folder)
    base, _ = os.path.splitext(video)
    log_path = os.path.join(folder_path, f'{base}.log')
    print(f"[DEBUG] Looking for log_path: {log_path}")
    logs = []
    # Fallback: if .log for requested video doesn't exist, try any .log file with the same base name
    if not os.path.exists(log_path):
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
        print(f"[DEBUG] No log file found for {base} in {folder_path}")
    print(f"[DEBUG] Returning {len(logs)} log entries")
    return jsonify(logs)

@app.route('/get-logs')
def get_logs_alias():
    return api_get_logs()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
