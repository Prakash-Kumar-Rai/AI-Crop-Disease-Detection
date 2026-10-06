"""
Plant & Foliage Verification Engine.
Validates whether an uploaded image contains a legitimate plant leaf,
preventing non-plant images (humans, pets, cars, furniture, screens, gym gear)
from being misclassified as crop diseases.
"""

import numpy as np
from PIL import Image
import tensorflow as tf
from tensorflow.keras.applications.mobilenet_v2 import (
    MobileNetV2,
    decode_predictions,
    preprocess_input
)

# Global lazy-loaded ImageNet model
_IMAGENET_MODEL = None

NON_PLANT_KEYWORDS = {
    # Humans, apparel, sports & personal items
    'person': 'Human subject',
    'man': 'Human subject',
    'woman': 'Human subject',
    'suit': 'Clothing / Person',
    'jersey': 'Athletic apparel',
    'wig': 'Apparel / Person',
    'sunglasses': 'Accessories',
    'swimming_trunks': 'Clothing / Swimwear',
    'dumbbell': 'Gym equipment',
    'barbell': 'Gym equipment',
    'punching_bag': 'Sports equipment',
    'diaper': 'Personal item',
    'brassiere': 'Apparel',
    'pajamas': 'Clothing',
    'jean': 'Clothing',
    'sweatshirt': 'Clothing',
    'trench_coat': 'Clothing',
    't-shirt': 'Clothing',
    'necktie': 'Clothing',
    'bow_tie': 'Clothing',
    'scuba_diver': 'Person in scuba gear',
    'military_uniform': 'Uniform / Person',
    'groom': 'Person / Formalwear',
    'gown': 'Clothing',
    'cloak': 'Clothing',
    'face_powder': 'Cosmetics',
    'lipstick': 'Cosmetics',
    'miniskirt': 'Clothing',
    'sock': 'Clothing',
    'shoe': 'Footwear',
    'running_shoe': 'Footwear',
    'sandal': 'Footwear',
    'boot': 'Footwear',
    'crash_helmet': 'Safety helmet',

    # Animals & Pets
    'dog': 'Domestic pet (Dog)',
    'cat': 'Domestic pet (Cat)',
    'terrier': 'Dog breed',
    'retriever': 'Dog breed',
    'hound': 'Dog breed',
    'bulldog': 'Dog breed',
    'horse': 'Animal',
    'zebra': 'Animal',
    'cow': 'Farm animal',
    'ox': 'Farm animal',
    'sheep': 'Farm animal',
    'pig': 'Farm animal',
    'elephant': 'Wild animal',
    'bear': 'Wild animal',
    'lion': 'Wild animal',
    'tiger': 'Wild animal',
    'monkey': 'Animal',
    'bird': 'Bird',
    'parrot': 'Bird',
    'snake': 'Reptile',
    'fish': 'Aquatic animal',

    # Electronics & Screens
    'cellular_telephone': 'Mobile phone / Device',
    'dial_telephone': 'Telephone',
    'computer': 'Computer / Electronics',
    'laptop': 'Laptop computer',
    'notebook': 'Laptop / Notebook',
    'keyboard': 'Computer keyboard',
    'mouse': 'Computer mouse',
    'monitor': 'Display monitor',
    'screen': 'Screen display',
    'television': 'Television display',
    'ipod': 'Electronic device',
    'remote_control': 'Remote control',

    # Vehicles & Transportation
    'car': 'Motor vehicle',
    'automobile': 'Motor vehicle',
    'sports_car': 'Sports vehicle',
    'jeep': 'Motor vehicle',
    'truck': 'Truck vehicle',
    'trailer': 'Vehicle trailer',
    'bus': 'Transit vehicle',
    'cab': 'Taxi vehicle',
    'motorcycle': 'Motorcycle',
    'bicycle': 'Bicycle',
    'airplane': 'Aircraft',
    'airliner': 'Airplane',
    'space_shuttle': 'Aerospace vehicle',
    'speedboat': 'Watercraft',

    # Furniture & Indoor Household
    'chair': 'Furniture',
    'table': 'Furniture',
    'desk': 'Desk / Table',
    'couch': 'Furniture / Sofa',
    'sofa': 'Furniture / Sofa',
    'bed': 'Bedroom furniture',
    'wardrobe': 'Furniture',
    'bookcase': 'Furniture',
    'pillow': 'Household item',
    'quilt': 'Bedding',
    'refrigerator': 'Appliance',
    'microwave': 'Kitchen appliance',
    'coffee_mug': 'Kitchenware',
    'beer_glass': 'Drinkware',
    'wine_bottle': 'Bottle / Beverage',
    'plate': 'Dinnerware'
}

PLANT_KEYWORDS = {
    'pot', 'flowerpot', 'daisy', 'yellow_lady', 'cardoon', 'artichoke',
    'head_cabbage', 'broccoli', 'cauliflower', 'zucchini', 'spaghetti_squash',
    'acorn_squash', 'butternut_squash', 'cucumber', 'bell_pepper', 'mushroom',
    'greenhouse', 'corn', 'ear', 'hay', 'fig', 'orange', 'lemon', 'banana',
    'pomegranate', 'custard_apple', 'strawberry', 'pineapple', 'tree', 'leaf', 'plant'
}


def get_imagenet_model():
    """Lazily loads and caches the MobileNetV2 ImageNet classifier."""
    global _IMAGENET_MODEL
    if _IMAGENET_MODEL is None:
        print("[*] Initializing Plant Verification Engine (ImageNet)...")
        _IMAGENET_MODEL = MobileNetV2(weights='imagenet')
        print("[+] Plant Verification Engine ready!")
    return _IMAGENET_MODEL


def compute_foliage_pigment_ratio(pil_img: Image.Image) -> float:
    """
    Analyzes botanical color pigments:
    - Green chlorophyll: Excess Green Index (2G - R - B)
    - Yellow/Brown diseased foliage pigments (carotenoids/necrosis)
    Returns percentage of pixels matching botanical plant tissue (0.0 to 1.0).
    """
    small = pil_img.convert("RGB").resize((100, 100))
    arr = np.array(small, dtype=np.float32) / 255.0
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

    # Chlorophyll green foliage mask
    exg = 2.0 * g - r - b
    green_mask = (exg > 0.04) & (g > r * 0.75) & (g > b * 0.75)

    # Yellowing/Brown chlorosis & necrotic leaf tissue
    necrosis_mask = (
        (r > 0.28) & (g > 0.22) & (b < 0.40) &
        (r > b * 1.25) & (g > b * 0.95) & (np.abs(r - g) < 0.25)
    )

    plant_pixels = np.sum(green_mask | necrosis_mask)
    return float(plant_pixels) / 10000.0


def verify_image_is_plant(image_path: str) -> dict:
    """
    Evaluates whether an image contains plant/leaf tissue or a non-plant subject.
    Returns:
        {
            "is_plant": bool,
            "detected_subject": str,
            "reason": str,
            "foliage_ratio": float,
            "non_plant_score": float
        }
    """
    try:
        img = Image.open(image_path).convert("RGB")
    except Exception as e:
        return {
            "is_plant": False,
            "detected_subject": "Corrupt or Unreadable File",
            "reason": f"Unable to read the image file: {str(e)}",
            "foliage_ratio": 0.0,
            "non_plant_score": 1.0
        }

    foliage_ratio = compute_foliage_pigment_ratio(img)

    # Fast rejection: Images with virtually zero plant pigmentation (< 1.5%)
    if foliage_ratio < 0.015:
        # Still run ImageNet to give an exact name to what was detected
        pass

    # Run semantic object detection
    model = get_imagenet_model()
    arr = preprocess_input(
        np.expand_dims(np.array(img.resize((224, 224)), dtype=np.float32), 0)
    )
    preds = model.predict(arr, verbose=0)
    top5 = decode_predictions(preds, top=5)[0]

    non_plant_score = 0.0
    plant_score = 0.0
    detected_descriptions = []
    first_non_plant_desc = None

    for _, label, prob in top5:
        lbl_lower = label.lower()
        is_np = False

        for kw, desc in NON_PLANT_KEYWORDS.items():
            if kw in lbl_lower:
                non_plant_score += prob
                is_np = True
                if not first_non_plant_desc:
                    first_non_plant_desc = desc
                break

        for kw in PLANT_KEYWORDS:
            if kw in lbl_lower:
                plant_score += prob
                break

        detected_descriptions.append(f"{label.replace('_', ' ').title()} ({prob*100:.1f}%)")

    # Decision Matrix:
    # 1. Non-plant objects (person, gym equipment, car, device, pet) with low foliage:
    is_non_plant = False
    rejection_reason = None
    detected_subject = "Crop Leaf"

    if (non_plant_score > 0.15 and foliage_ratio < 0.08) or (non_plant_score > 0.40 and plant_score < 0.05):
        is_non_plant = True
        subject = first_non_plant_desc or detected_descriptions[0].split(" (")[0]
        detected_subject = subject
        rejection_reason = (
            f"Our AI vision filter detected {subject} in this image rather than a crop leaf. "
            f"Detected subjects: {', '.join(detected_descriptions[:2])}."
        )
    elif foliage_ratio < 0.02:
        is_non_plant = True
        detected_subject = detected_descriptions[0].split(" (")[0]
        rejection_reason = (
            f"The image does not contain sufficient leaf or plant pigmentation. "
            f"Identified as: {detected_subject}."
        )

    return {
        "is_plant": not is_non_plant,
        "detected_subject": detected_subject,
        "reason": rejection_reason,
        "foliage_ratio": round(foliage_ratio * 100, 2),
        "non_plant_score": round(non_plant_score * 100, 2),
        "top_labels": detected_descriptions[:3]
    }
