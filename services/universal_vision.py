"""
Universal Multimodal AI Vision Engine for AgriVision AI.
Capable of identifying ANY botanical plant species and ANY crop disease on Earth
using Google Gemini Multimodal Vision.
"""

import os
import json
import base64
import requests
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv

load_dotenv()


def diagnose_universal_plant(image_path: str, user_crop_hint: str = None, custom_api_key: str = None) -> dict:
    """
    Performs universal botanical diagnosis on any plant and disease on Earth
    using Gemini Multimodal Vision API.
    """
    api_key = custom_api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {
            "success": False,
            "error_type": "MISSING_API_KEY",
            "message": "A free Google Gemini API Key is required for Universal AI Mode (diagnosing any plant in the world). Add your key in the header settings or in .env."
        }

    # Prepare image in base64
    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        
        # Determine mime type
        ext = os.path.splitext(image_path)[1].lower().replace(".", "")
        if ext in ("jpg", "jpeg"):
            mime_type = "image/jpeg"
        elif ext == "png":
            mime_type = "image/png"
        elif ext == "webp":
            mime_type = "image/webp"
        else:
            mime_type = "image/jpeg"
    except Exception as e:
        return {
            "success": False,
            "error_type": "IMAGE_READ_ERROR",
            "message": f"Unable to read image for vision analysis: {str(e)}"
        }

    crop_context_note = f" (User specified hint: {user_crop_hint})" if user_crop_hint and user_crop_hint != "auto" and user_crop_hint != "any" else ""

    prompt = (
        "You are an expert plant pathologist and agronomist. Analyze this leaf/plant image accurately"
        f"{crop_context_note}.\n"
        "1. Verify if this image is a plant/leaf. If not, state clearly.\n"
        "2. Identify the exact plant common name and scientific botanical name (e.g. 'Mango (Mangifera indica)', 'Rice (Oryza sativa)', 'Rose (Rosa)', 'Tomato (Solanum lycopersicum)').\n"
        "3. Detect any disease, pest infestation, abiotic stress, or if it is healthy.\n"
        "4. Provide a structured diagnosis and practical agronomic treatment prescription.\n\n"
        "Return ONLY a valid JSON object with this exact structure:\n"
        "{\n"
        '  "is_plant": true,\n'
        '  "plant_name": "Common Name",\n'
        '  "scientific_name": "Scientific Name",\n'
        '  "condition": "Disease Name or Healthy Plant",\n'
        '  "is_healthy": false,\n'
        '  "severity": "Mild" | "Moderate" | "Severe" | "None",\n'
        '  "confidence": 94.5,\n'
        '  "overview": "2-3 sentences explaining the pathology, causes, and progression.",\n'
        '  "symptoms": ["Symptom 1", "Symptom 2", "Symptom 3"],\n'
        '  "organic_remedies": ["Organic remedy 1", "Organic remedy 2"],\n'
        '  "chemical_treatments": ["Chemical fungicide/pesticide 1", "Chemical treatment 2"],\n'
        '  "prevention": ["Cultural preventive tip 1", "Cultural tip 2"],\n'
        '  "soil_nutrients": ["Soil/Fertilizer recommendation 1", "Nutrient tip 2"],\n'
        '  "irrigation": ["Watering guidance 1", "Moisture tip 2"]\n'
        "}"
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": encoded_image
                        }
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json"
        }
    }

    try:
        res = requests.post(url, json=payload, timeout=18)
        if res.status_code == 200:
            data = res.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(raw_text)

            if not parsed.get("is_plant", True):
                return {
                    "success": False,
                    "error_type": "NON_PLANT",
                    "detected_subject": parsed.get("condition", "Non-plant subject"),
                    "message": "Universal AI Vision confirmed that this image does not contain a plant or crop leaf."
                }

            return {
                "success": True,
                "data": {
                    "crop": parsed.get("plant_name", "Identified Plant"),
                    "scientific_name": parsed.get("scientific_name", ""),
                    "disease": parsed.get("condition", "Unknown Condition"),
                    "is_healthy": parsed.get("is_healthy", False),
                    "severity": parsed.get("severity", "Moderate"),
                    "confidence": f"{float(parsed.get('confidence', 92.0)):.2f}%",
                    "overview": parsed.get("overview", "Comprehensive plant health analysis generated via Universal AI Vision."),
                    "symptoms": parsed.get("symptoms", []),
                    "organic_remedies": parsed.get("organic_remedies", []),
                    "chemical_treatments": parsed.get("chemical_treatments", []),
                    "prevention": parsed.get("prevention", []),
                    "soil_nutrients": parsed.get("soil_nutrients", []),
                    "irrigation": parsed.get("irrigation", []),
                    "source": "Universal Multimodal AI Vision (Gemini 2.5 Flash)"
                }
            }
        else:
            error_data = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
            err_msg = error_data.get("error", {}).get("message", f"HTTP {res.status_code}")
            return {
                "success": False,
                "error_type": "API_ERROR",
                "message": f"Gemini Vision API error: {err_msg}"
            }
    except Exception as e:
        return {
            "success": False,
            "error_type": "REQUEST_ERROR",
            "message": f"Network error during Universal Vision request: {str(e)}"
        }

