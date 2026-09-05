# 🌱 AI Crop Disease Detection

An AI-powered web application that detects crop diseases from leaf
images using a deep learning model based on **MobileNetV2** and
**TensorFlow/Keras**.

The project provides a simple Flask web interface where users can upload
a crop leaf image and receive the predicted disease along with the model
confidence, symptoms, prevention tips, and management advice.

------------------------------------------------------------------------

## 🚀 Features

-   🌱 AI-based crop disease detection (MobileNetV2 Transfer Learning)
-   📸 Upload crop leaf images from local disk
-   🌐 **Internet Image URL Input**: Paste any direct image URL from the web to analyze instantly
-   🔍 Automatic disease prediction across 38 crop & disease classes
-   📊 Confidence percentage and animated progress bar
-   ⚠️ Low-confidence warning for uncertain predictions
-   🤖 **Live Online Agronomic Intelligence**:
    -   Connects with **Google Gemini AI** for tailored agricultural recommendations
    -   Live Wikipedia REST API lookup for pathogen pathology and background
    -   Comprehensive 38-class agronomic guide with symptoms, organic remedies, chemical controls, and prevention
-   🍃 **Organic & Biological Treatments**: Natural remedies, composts, and biocontrols
-   🧪 **Chemical Controls & Fungicides**: Registered fungicides and spray recommendations
-   🛡️ **Preventative Agricultural Practices**: Crop rotation, pruning, and moisture control
-   📱 **Local Network / Mobile Access**: Hosted on `0.0.0.0` so phones on the same Wi-Fi can open the app
-   🌍 **Public Internet Sharing**: One-command public HTTPS tunnel (`python run_public.py`) to share globally
-   🔄 Try Another Image button & instant image previews
-   🖥️ Offline fallback support: Works completely offline when no internet is available

------------------------------------------------------------------------

## 🧠 Machine Learning Model

The project uses **MobileNetV2** with transfer learning.

### Model details

-   Framework: TensorFlow / Keras
-   Architecture: MobileNetV2
-   Input image size: `224 × 224`
-   Number of classes: **38**
-   Training images: **43,444**
-   Validation images: **10,861**
-   Total dataset images: **54,305**
-   Validation accuracy: **95.01%**
-   Model file: `model/disease_model.keras`

The MobileNetV2 base is used as a feature extractor and a classification
layer is added for the 38 crop-disease classes.

------------------------------------------------------------------------

## 🌾 Supported Classes

The model supports the following 38 classes:

1.  Apple - Apple Scab
4.  Apple - Healthy
5.  Blueberry - Healthy
6.  Cherry - Powdery Mildew
7.  Cherry - Healthy
8.  Corn - Cercospora Leaf Spot / Gray Leaf Spot
9.  Corn - Common Rust
10. Corn - Northern Leaf Blight
11. Corn - Healthy
12. Grape - Black Rot
13. Grape - Esca / Black Measles
14. Grape - Leaf Blight
15. Grape - Healthy
16. Orange - Haunglongbing / Citrus Greening
17. Peach - Bacterial Spot
18. Peach - Healthy
19. Pepper Bell - Bacterial Spot
20. Pepper Bell - Healthy
21. Potato - Early Blight
22. Potato - Late Blight
23. Potato - Healthy
24. Raspberry - Healthy
25. Soybean - Healthy
26. Squash - Powdery Mildew
27. Strawberry - Leaf Scorch
28. Strawberry - Healthy
29. Tomato - Bacterial Spot
30. Tomato - Early Blight
31. Tomato - Late Blight
32. Tomato - Leaf Mold
33. Tomato - Septoria Leaf Spot
34. Tomato - Spider Mites
35. Tomato - Target Spot
36. Tomato - Tomato Yellow Leaf Curl Virus
37. Tomato - Tomato Mosaic Virus
38. Tomato - Healthy

------------------------------------------------------------------------

## 📂 Project Structure

``` text
AI-Crop-Disease-Detection/
│
├── dataset/
│   ├── Apple___Apple_scab/
│   ├── Apple___Black_rot/
│   ├── ...
│   └── Tomato___healthy/
│
├── model/
│   ├── class_names.json
│   └── disease_model.keras
│
├── services/
│   ├── __init__.py
│   └── internet_service.py
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js
│
├── templates/
│   └── index.html
│
├── uploads/
├── venv/
├── .env.example
├── app.py
├── run_public.py
├── train_model.py
├── requirements.txt
└── README.md
```

------------------------------------------------------------------------

## ⚙️ Technologies Used

### Programming Language

-   Python

### Machine Learning

-   TensorFlow
-   Keras
-   MobileNetV2
-   NumPy
-   Pillow

### Web Development

-   Flask
-   HTML5
-   CSS3
-   JavaScript

### Dataset

-   PlantVillage Dataset

------------------------------------------------------------------------

## 🛠️ Installation

### 1. Clone or download the project

Open PowerShell or the VS Code terminal:

``` powershell
git clone <your-repository-url>
cd AI-Crop-Disease-Detection
```

If the project is already downloaded, simply open the project folder in
VS Code.

------------------------------------------------------------------------

### 2. Create a virtual environment

``` powershell
python -m venv venv
```

Activate it:

``` powershell
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:

``` powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

Then activate again:

``` powershell
.\venv\Scripts\Activate.ps1
```

------------------------------------------------------------------------

### 3. Install dependencies

``` powershell
python -m pip install --upgrade pip
```

Then:

``` powershell
python -m pip install tensorflow numpy pillow flask scikit-learn matplotlib
```

------------------------------------------------------------------------

## 🧪 Verify Installation

Check TensorFlow:

``` powershell
python -c "import tensorflow; print('TensorFlow:', tensorflow.__version__)"
```

Check Flask:

``` powershell
python -c "import flask; print('Flask installed successfully')"
```

Check Pillow:

``` powershell
python -c "from PIL import Image; print('Pillow installed successfully')"
```

------------------------------------------------------------------------

## 🧠 Training the Model

If the trained model is not already present, make sure the dataset is
inside:

``` text
dataset/
```

Then run:

``` powershell
python train_model.py
```

The training script creates the trained model:

``` text
model/disease_model.keras
```

The project used 10 training epochs and achieved approximately:

``` text
Validation Accuracy: 95.01%
Validation Loss: 0.1555
```

> Training on CPU can take a long time. The first MobileNetV2 setup may
> also download pretrained weights.

------------------------------------------------------------------------

## ▶️ Running the Application

Activate the virtual environment:

``` powershell
.\venv\Scripts\Activate.ps1
```

### Option A: Standard Run (Local & Local Network / Wi-Fi Access)

Start Flask:

``` powershell
python app.py
```

You will see:

``` text
============================================================
AI Crop Disease Detection Server Started!
[*] Local Access:          http://127.0.0.1:5000
[*] Network/Mobile Access: http://192.168.x.x:5000
[*] Internet Public Access: Run 'python run_public.py' to share worldwide!
============================================================
```

- **From your PC**: Open [http://127.0.0.1:5000](http://127.0.0.1:5000)
- **From your Smartphone or Laptop on the same Wi-Fi**: Open `http://<Network-IP>:5000` (e.g., `http://192.168.1.15:5000`)

---

### Option B: Public Internet Access (Share Worldwide)

To make your crop disease detector accessible to anyone in the world over the internet:

``` powershell
python run_public.py
```

This launches a public HTTPS tunnel (via `pyngrok`). You will see:

``` text
SUCCESS! Your app is live on the internet at:
>>> https://xxxx-xx-xx.ngrok-free.app <<<
```

Anyone with the link can open the application on their phone or computer!

> **Note**: You can optionally configure your free Ngrok auth token in `.env` to prevent session timeouts.
> Alternatively, you can run: `npx localtunnel --port 5000`.

---

## 🤖 Optional: Configuring Google Gemini AI API

The app connects to the internet to enrich detected crop diseases with real-time agronomic intelligence, symptoms, organic remedies, and chemical controls.

- **Without API Key (Zero Setup)**: The app automatically pulls live disease pathology from the **Wikipedia REST API** and our built-in 38-class agronomic knowledge base.
- **With Gemini AI (Advanced)**: Copy `.env.example` to `.env`:
  ```bash
  copy .env.example .env
  ```
  Edit `.env` and add your free Gemini API key:
  ```env
  GEMINI_API_KEY=your_actual_gemini_api_key
  ```
  The app will now consult Gemini AI live for every detected disease!

------------------------------------------------------------------------

## 🔍 How It Works

``` text
User uploads leaf image
          ↓
Flask receives image
          ↓
Image preprocessing
          ↓
Resize to 224 × 224
          ↓
TensorFlow / MobileNetV2 model
          ↓
Prediction probabilities
          ↓
Highest probability class selected
          ↓
Disease + confidence displayed
          ↓
Symptoms / Prevention / Management
```

------------------------------------------------------------------------

## 📊 Example Result

For example, the application may return:

``` text
Disease: Tomato Late Blight
Confidence: 99.19%
```

The application then displays relevant information such as:

-   Symptoms
-   Prevention
-   Management advice

The confidence value represents the model's estimated probability for
the predicted class and should not be treated as a guaranteed diagnosis.

------------------------------------------------------------------------

## ⚠️ Important Note

This project is an **academic AI/ML project** and is intended for
demonstration and educational purposes.

A model prediction should not be treated as a definitive agricultural
diagnosis. For real crop-treatment decisions, consult a qualified
agricultural professional and follow locally approved guidance and
product-label instructions.

------------------------------------------------------------------------

## 🔧 Troubleshooting

### TensorFlow cannot be installed

Use a supported Python version for the TensorFlow build you are
installing. For this project, Python **3.12.x** was used successfully.

Check:

``` powershell
python --version
```

or:

``` powershell
py -3.12 --version
```

------------------------------------------------------------------------

### Flask not found

Activate the virtual environment and install Flask:

``` powershell
.\venv\Scripts\Activate.ps1
python -m pip install flask
```

------------------------------------------------------------------------

### Model not found

Make sure this file exists:

``` text
model/disease_model.keras
```

If it does not exist, train the model:

``` powershell
python train_model.py
```

------------------------------------------------------------------------

### Dataset not found

Make sure the dataset structure looks like:

``` text
dataset/
├── Apple___Apple_scab/
├── Apple___Black_rot/
├── Apple___healthy/
├── ...
└── Tomato___healthy/
```

------------------------------------------------------------------------

## 📈 Future Improvements

Possible future enhancements include:

-   📱 Mobile application
-   ☁️ Cloud deployment
-   🔐 User authentication
-   📜 Prediction history
-   📥 PDF report generation
-   📊 Disease statistics dashboard
-   🌍 Multi-language support
-   🌾 More crop varieties
-   🤖 Improved model architecture
-   📷 Camera-based live detection
-   🗺️ Location-based agricultural guidance

------------------------------------------------------------------------

## 🎓 Academic Information

**Project:** AI Crop Disease Detection

**Course:** B.Tech Computer Science & Engineering

**Project Type:** Engineering / Final-Year Project

**University:** Quantum University

------------------------------------------------------------------------

## 👨‍💻 Author

**Prakash Kumar**

B.Tech CSE\
Quantum University

------------------------------------------------------------------------

## 📄 License

This project is intended primarily for educational and academic use.

Check the licenses and terms of the underlying dataset, pretrained model
weights, and third-party libraries before redistributing the complete
project or dataset.
