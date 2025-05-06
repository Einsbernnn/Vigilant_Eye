from flask import Flask, send_from_directory, jsonify, request, send_file
from flask_cors import CORS
import os
import time
import shutil

app = Flask(__name__)
CORS(app)

KNOWN_FACES_DIR = '/home/einsbern/facial_recognition/dataset'
VIDEO_DIR = '/home/einsbern/facial_recognition/footage'

@app.route('/api/images')
def list_images():
    files = [f for f in os.listdir(KNOWN_FACES_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    return jsonify(files)

@app.route('/known_faces/<filename>')
def serve_image(filename):
    return send_from_directory(
        KNOWN_FACES_DIR,
        filename,
        as_attachment=False
    )

@app.route('/api/upload', methods=['POST'])
def upload_images():
    folder = request.form.get('folder')  # Get folder name from frontend
    if not folder:
        return jsonify({"error": "No folder specified"}), 400

    target_folder = os.path.join(KNOWN_FACES_DIR, folder)
    os.makedirs(target_folder, exist_ok=True)  # Create folder if not exists

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
    folder = request.form.get('folder')  # Get folder name from frontend
    if not folder:
        return jsonify({"error": "No folder specified"}), 400

    target_folder = os.path.join(VIDEO_DIR, folder)
    os.makedirs(target_folder, exist_ok=True)  # Create folder if not exists

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
    folders = []
    for entry in os.scandir(VIDEO_DIR):
        if entry.is_dir():
            folders.append(entry.name)
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
    return jsonify(videos)

@app.route('/api/image-folders')
def list_image_folders():
    folders = []
    for entry in os.scandir(KNOWN_FACES_DIR):
        if entry.is_dir():
            folders.append(entry.name)
    return jsonify(folders)

@app.route('/api/video-folders')
def list_video_folders():
    folders = []
    for entry in os.scandir(VIDEO_DIR):
        if entry.is_dir():
            folders.append(entry.name)
    return jsonify(folders)

@app.route('/dataset/<folder>/<filename>')
def serve_folder_image(folder, filename):
    folder_path = os.path.join(KNOWN_FACES_DIR, folder)
    return send_from_directory(folder_path, filename, as_attachment=False)

@app.route('/api/rename-folder', methods=['POST'])
def rename_folder():
    data = request.json
    folder_type = data.get('type')  # 'image' or 'video'
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
    folder_type = data.get('type')  # 'image' or 'video'
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
    folder_type = request.args.get('type')  # 'image' or 'video'
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
