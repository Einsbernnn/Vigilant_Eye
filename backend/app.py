from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
import os
import time

app = Flask(__name__)
CORS(app)  # <-- Add this line

KNOWN_FACES_DIR = '/home/einsbern/known_faces'

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
    if 'images' not in request.files:
        return jsonify({"error": "No files part"}), 400

    files = request.files.getlist('images')
    saved = []
    for file in files:
        if file and file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            save_path = os.path.join(KNOWN_FACES_DIR, file.filename)
            file.save(save_path)
            saved.append(file.filename)
    return jsonify({"uploaded": saved}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
