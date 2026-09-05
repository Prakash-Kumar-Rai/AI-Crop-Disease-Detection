import os
import json
import socket
import numpy as np
import tensorflow as tf
from PIL import Image
from flask import Flask, render_template, request, send_from_directory
from dotenv import load_dotenv

from services.internet_service import (
    download_image_from_url,
    fetch_online_disease_info,
    parse_class_name,
)

import sys

# Ensure safe UTF-8 output on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

app = Flask(__name__)

# ==============================
# CONFIGURATION
# ==============================
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
MODEL_PATH = "model/disease_model.keras"
CLASS_NAMES_PATH = "model/class_names.json"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ==============================
# LOAD AI MODEL & LABELS
# ==============================
print("[*] Loading AI model...")
model = tf.keras.models.load_model(MODEL_PATH)
print("[+] AI model loaded successfully!")

with open(CLASS_NAMES_PATH, "r", encoding="utf-8") as file:
    class_names = json.load(file)
print(f"[+] Loaded {len(class_names)} disease classes.")


# ==============================
# ROUTES
# ==============================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/predict", methods=["POST"])
def predict():
    image_source_type = request.form.get("source_type", "file")
    image_url_input = request.form.get("image_url", "").strip()
    image_path = None
    display_image_url = None

    try:
        # 1. Handle Internet URL input
        if image_source_type == "url" or (image_url_input and not request.files.get("image")):
            if not image_url_input:
                return render_template(
                    "index.html",
                    error="Please provide a valid image URL from the internet."
                )

            image_path = download_image_from_url(
                image_url_input,
                app.config["UPLOAD_FOLDER"]
            )
            filename = os.path.basename(image_path)
            display_image_url = f"/uploads/{filename}"

        # 2. Handle File Upload
        else:
            if "image" not in request.files:
                return render_template(
                    "index.html",
                    error="Please select an image file to upload."
                )

            image_file = request.files["image"]
            if image_file.filename == "":
                return render_template(
                    "index.html",
                    error="Please select an image file to upload."
                )

            # Secure/clean filename
            safe_filename = f"upload_{os.path.basename(image_file.filename)}"
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_filename)
            image_file.save(image_path)
            display_image_url = f"/uploads/{safe_filename}"

        # ==============================
        # IMAGE PREPROCESSING
        # ==============================
        image = Image.open(image_path).convert("RGB")
        image = image.resize((224, 224))
        image_array = np.array(image, dtype=np.float32)
        image_array = np.expand_dims(image_array, axis=0)

        # ==============================
        # AI PREDICTION
        # ==============================
        predictions = model.predict(image_array, verbose=0)
        predicted_index = int(np.argmax(predictions[0]))
        confidence = float(predictions[0][predicted_index] * 100)
        raw_disease_class = class_names[predicted_index]

        # ==============================
        # INTERNET AGRONOMIC INTELLIGENCE
        # ==============================
        disease_info = fetch_online_disease_info(raw_disease_class)

        return render_template(
            "index.html",
            prediction=raw_disease_class,
            confidence=f"{confidence:.2f}%",
            disease_info=disease_info,
            analyzed_image=display_image_url
        )

    except ValueError as ve:
        return render_template("index.html", error=str(ve))
    except Exception as error:
        print("Prediction Error:", error)
        return render_template(
            "index.html",
            error="Unable to analyze the image. Please make sure it is a valid leaf photo."
        )


# ==============================
# RUN APPLICATION
# ==============================

def get_local_ip():
    """Returns the local LAN IP address for phone/device connection."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "0.0.0.0")
    local_ip = get_local_ip()

    print("\n" + "=" * 60)
    print("AI Crop Disease Detection Server Started!")
    print(f"[*] Local Access:          http://127.0.0.1:{port}")
    print(f"[*] Network/Mobile Access: http://{local_ip}:{port}")
    print("[*] Internet Public Access: Run 'python run_public.py' to share worldwide!")
    print("=" * 60 + "\n")

    app.run(
        host=host,
        port=port,
        debug=True
    )