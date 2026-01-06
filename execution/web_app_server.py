import os
import uuid
from flask import Flask, request, jsonify, send_from_directory
from process_pdf_watermark import remove_watermarks
from process_image_watermark import remove_gemini_watermark
from cleanup_temp_files import cleanup_old_files

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder=os.path.join(BASE_DIR, "../web"), static_url_path="")

UPLOAD_FOLDER = os.path.normpath(os.path.join(BASE_DIR, "../.tmp/uploads"))
PROCESSED_FOLDER = os.path.normpath(os.path.join(BASE_DIR, "../.tmp/processed"))

ALLOWED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg'}

for folder in [UPLOAD_FOLDER, PROCESSED_FOLDER]:
    os.makedirs(folder, exist_ok=True)

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    # Cleanup old files on every upload request or use a background thread
    cleanup_old_files(UPLOAD_FOLDER)
    cleanup_old_files(PROCESSED_FOLDER)

    if "file" not in request.files:
        return jsonify({"success": False, "message": "No file part"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "message": "No selected file"}), 400

    filename = f"{uuid.uuid4()}_{file.filename}"
    ext = os.path.splitext(filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"success": False, "message": f"Extension {ext} not allowed"}), 400

    input_path = os.path.join(UPLOAD_FOLDER, filename)
    output_filename = f"cleaned_{filename}"
    output_path = os.path.join(PROCESSED_FOLDER, output_filename)

    file.save(input_path)

    if ext == '.pdf':
        success, message, result_path = remove_watermarks(input_path, output_path)
    else:
        # It's an image
        success, message, result_path = remove_gemini_watermark(input_path, output_path)

    if success:
        return jsonify({
            "success": True, 
            "message": message, 
            "download_url": f"/download/{output_filename}"
        })
    else:
        return jsonify({"success": False, "message": message}), 500

@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(PROCESSED_FOLDER, filename, as_attachment=True)

if __name__ == "__main__":
    # Use PORT from environment (like Render does) or default to 5001
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
