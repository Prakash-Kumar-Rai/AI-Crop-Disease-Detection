import os
import sys
import json
import socket
import base64
import time
import shutil
import numpy as np
import tensorflow as tf
from PIL import Image
from flask import Flask, render_template, request, send_from_directory
from dotenv import load_dotenv

from services.internet_service import (
    download_image_from_url,
    fetch_online_disease_info,
    parse_class_name,
    CROP_CATALOG,
)
from services.plant_verifier import verify_image_is_plant

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
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
MODEL_PATH = os.path.join(BASE_DIR, "model", "disease_model.keras")
CLASS_NAMES_PATH = os.path.join(BASE_DIR, "model", "class_names.json")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ==============================
# LOAD AI MODEL & LABELS
# ==============================
print("[*] Loading AI crop disease detection model...")
model = tf.keras.models.load_model(MODEL_PATH)
print("[+] AI model loaded successfully!")

with open(CLASS_NAMES_PATH, "r", encoding="utf-8") as file:
    class_names = json.load(file)
print(f"[+] Loaded {len(class_names)} disease classes across 14 crops.")


# ==============================
# ROUTES
# ==============================

@app.route("/")
def home():
    return render_template("index.html", crop_catalog=CROP_CATALOG)


@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/predict", methods=["POST"])
def predict():
    image_source_type = request.form.get("source_type", "file")
    target_crop = request.form.get("target_crop", "auto").strip().lower()
    image_path = None
    display_image_url = None

    try:
        # 1. Handle Live Camera Capture (Base64 data URL)
        if image_source_type == "camera":
            camera_data = request.form.get("camera_image", "").strip()
            if not camera_data or "," not in camera_data:
                return render_template(
                    "index.html",
                    error="No camera snapshot captured. Please snap a photo using the camera.",
                    crop_catalog=CROP_CATALOG,
                    target_crop=target_crop
                )

            header, encoded = camera_data.split(",", 1)
            raw_bytes = base64.b64decode(encoded)
            filename = f"cam_{int(time.time())}.jpg"
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            with open(image_path, "wb") as f:
                f.write(raw_bytes)
            display_image_url = f"/uploads/{filename}"

        # 2. Handle Demo Quick Sample Images
        elif image_source_type == "sample":
            sample_name = request.form.get("sample_image", "").strip()
            sample_source = os.path.join(BASE_DIR, "static", "samples", sample_name)
            if not os.path.exists(sample_source):
                return render_template(
                    "index.html",
                    error="Sample image not found on server.",
                    crop_catalog=CROP_CATALOG,
                    target_crop=target_crop
                )
            dest_name = f"sample_{int(time.time())}_{sample_name}"
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], dest_name)
            shutil.copy2(sample_source, image_path)
            display_image_url = f"/uploads/{dest_name}"

        # 3. Handle Internet Image URL
        elif image_source_type == "url":
            image_url_input = request.form.get("image_url", "").strip()
            if not image_url_input:
                return render_template(
                    "index.html",
                    error="Please provide a valid image URL from the internet.",
                    crop_catalog=CROP_CATALOG,
                    target_crop=target_crop
                )
            image_path = download_image_from_url(
                image_url_input,
                app.config["UPLOAD_FOLDER"]
            )
            filename = os.path.basename(image_path)
            display_image_url = f"/uploads/{filename}"

        # 4. Handle Standard Local File Upload
        else:
            if "image" not in request.files:
                return render_template(
                    "index.html",
                    error="Please select a crop leaf image file to upload.",
                    crop_catalog=CROP_CATALOG,
                    target_crop=target_crop
                )

            image_file = request.files["image"]
            if image_file.filename == "":
                return render_template(
                    "index.html",
                    error="Please select a crop leaf image file to upload.",
                    crop_catalog=CROP_CATALOG,
                    target_crop=target_crop
                )

            safe_filename = f"upload_{int(time.time())}_{os.path.basename(image_file.filename)}"
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_filename)
            image_file.save(image_path)
            display_image_url = f"/uploads/{safe_filename}"

        # ==============================================================
        # STAGE 1: DUAL-LAYER PLANT & FOLIAGE VERIFICATION
        # ==============================================================
        plant_check = verify_image_is_plant(image_path)
        if not plant_check["is_plant"]:
            return render_template(
                "index.html",
                non_plant_detected=True,
                verification=plant_check,
                analyzed_image=display_image_url,
                crop_catalog=CROP_CATALOG,
                target_crop=target_crop
            )

        # ==============================================================
        # STAGE 2: PREPROCESS IMAGE & RUN DEEP LEARNING MODEL
        # ==============================================================
        image = Image.open(image_path).convert("RGB")
        image = image.resize((224, 224))
        image_array = np.array(image, dtype=np.float32)
        image_array = np.expand_dims(image_array, axis=0)

        predictions = model.predict(image_array, verbose=0)

        # ==============================================================
        # STAGE 3: CROP-TARGET DISAMBIGUATION & OUT-OF-DOMAIN CHECKS
        # ==============================================================
        is_unsupported_crop = False
        unsupported_message = None

        if target_crop != "auto" and target_crop in CROP_CATALOG:
            # Crop was specified by the user: filter predictions strictly to that crop!
            allowed_classes = CROP_CATALOG[target_crop]["classes"]
            allowed_indices = [class_names.index(c) for c in allowed_classes if c in class_names]

            if allowed_indices:
                crop_probs = [float(predictions[0][idx]) for idx in allowed_indices]
                sum_p = sum(crop_probs)
                if sum_p > 0:
                    norm_probs = [p / sum_p for p in crop_probs]
                    best_local = int(np.argmax(norm_probs))
                    predicted_index = allowed_indices[best_local]
                    confidence = float(norm_probs[best_local] * 100)
                else:
                    predicted_index = allowed_indices[0]
                    confidence = 50.0
            else:
                predicted_index = int(np.argmax(predictions[0]))
                confidence = float(predictions[0][predicted_index] * 100)
        else:
            # Auto-detect across all 38 classes
            predicted_index = int(np.argmax(predictions[0]))
            confidence = float(predictions[0][predicted_index] * 100)

            # Check if this leaf may belong to an unsupported plant species (like Mango, Rose, etc.)
            top_prob = float(predictions[0][predicted_index])
            top_crop_family = parse_class_name(class_names[predicted_index])[0]
            sorted_indices = np.argsort(predictions[0])[::-1]

            second_diff_prob = 0.0
            second_diff_crop = None
            for s_idx in sorted_indices[1:]:
                c_family = parse_class_name(class_names[s_idx])[0]
                if c_family.lower() != top_crop_family.lower():
                    second_diff_prob = float(predictions[0][s_idx])
                    second_diff_crop = c_family
                    break

            # If confidence is moderate/low (< 68%) or margin between different crops is narrow
            if confidence < 68.0 or ((top_prob - second_diff_prob) < 0.12):
                is_unsupported_crop = True
                unsupported_message = (
                    f"This leaf shows traits of {top_crop_family} ({confidence:.1f}%), but our AI detected uncertainty. "
                    "If your plant is an unsupported species (such as Mango, Guava, Rose, Basil, Neem, or a houseplant), "
                    "please note that our specialized model is trained for 14 agricultural crops."
                )

        raw_disease_class = class_names[predicted_index]

        # ==============================================================
        # STAGE 4: AGRONOMIC INTELLIGENCE & REMEDIES RETRIEVAL
        # ==============================================================
        disease_info = fetch_online_disease_info(raw_disease_class)

        return render_template(
            "index.html",
            prediction=raw_disease_class,
            confidence=f"{confidence:.2f}%",
            disease_info=disease_info,
            analyzed_image=display_image_url,
            crop_catalog=CROP_CATALOG,
            target_crop=target_crop,
            is_unsupported_crop=is_unsupported_crop,
            unsupported_message=unsupported_message,
            verification=plant_check
        )

    except ValueError as ve:
        return render_template(
            "index.html",
            error=str(ve),
            crop_catalog=CROP_CATALOG,
            target_crop=target_crop
        )
    except Exception as error:
        print("[!] Prediction Error:", error)
        return render_template(
            "index.html",
            error="Unable to analyze the image. Please make sure it is a valid leaf photo.",
            crop_catalog=CROP_CATALOG,
            target_crop=target_crop
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

    print("\n" + "=" * 65)
    print("🌱 AgriVision AI — Crop Disease Diagnostic Suite Started!")
    print(f"[*] Local PC Access:       http://127.0.0.1:{port}")
    print(f"[*] Mobile / Wi-Fi Access: http://{local_ip}:{port}")
    print("[*] Internet Tunnel:       Run 'python run_public.py' to share worldwide")
    print("=" * 65 + "\n")

    app.run(
        host=host,
        port=port,
        debug=True
    )