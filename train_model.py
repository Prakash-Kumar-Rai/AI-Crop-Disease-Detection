import os
import json
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

# ==============================
# CONFIGURATION
# ==============================

DATASET_DIR = "dataset"
MODEL_DIR = "model"

IMG_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 10
SEED = 42

os.makedirs(MODEL_DIR, exist_ok=True)

print("\n🌱 AI Crop Disease Detection")
print("=" * 45)

# ==============================
# LOAD DATASET
# ==============================

print("\n📂 Loading dataset...")

train_dataset = tf.keras.utils.image_dataset_from_directory(
    DATASET_DIR,
    validation_split=0.2,
    subset="training",
    seed=SEED,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE
)

validation_dataset = tf.keras.utils.image_dataset_from_directory(
    DATASET_DIR,
    validation_split=0.2,
    subset="validation",
    seed=SEED,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE
)

class_names = train_dataset.class_names
num_classes = len(class_names)

print(f"\n✅ Number of classes: {num_classes}")

print("\n📋 Classes:")
for i, class_name in enumerate(class_names):
    print(f"{i}: {class_name}")

# ==============================
# SAVE CLASS NAMES
# ==============================

class_names_path = os.path.join(
    MODEL_DIR,
    "class_names.json"
)

with open(class_names_path, "w") as f:
    json.dump(class_names, f, indent=4)

print("\n💾 Class names saved.")

# ==============================
# PERFORMANCE OPTIMIZATION
# ==============================

AUTOTUNE = tf.data.AUTOTUNE

train_dataset = train_dataset.prefetch(
    buffer_size=AUTOTUNE
)

validation_dataset = validation_dataset.prefetch(
    buffer_size=AUTOTUNE
)

# ==============================
# DATA AUGMENTATION
# ==============================

data_augmentation = tf.keras.Sequential([
    layers.RandomFlip("horizontal"),
    layers.RandomRotation(0.1),
    layers.RandomZoom(0.1),
    layers.RandomContrast(0.1)
])

# ==============================
# TRANSFER LEARNING MODEL
# ==============================

print("\n🧠 Loading MobileNetV2...")

base_model = MobileNetV2(
    input_shape=IMG_SIZE + (3,),
    include_top=False,
    weights="imagenet"
)

# Freeze pretrained layers
base_model.trainable = False

# ==============================
# BUILD MODEL
# ==============================

model = models.Sequential([

    data_augmentation,

    layers.Rescaling(
        1.0 / 127.5,
        offset=-1
    ),

    base_model,

    layers.GlobalAveragePooling2D(),

    layers.Dropout(0.2),

    layers.Dense(
        num_classes,
        activation="softmax"
    )
])

# ==============================
# COMPILE
# ==============================

model.compile(
    optimizer="adam",
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

model.summary()

# ==============================
# CALLBACKS
# ==============================

model_path = os.path.join(
    MODEL_DIR,
    "disease_model.keras"
)

callbacks = [

    EarlyStopping(
        monitor="val_accuracy",
        patience=3,
        restore_best_weights=True
    ),

    ModelCheckpoint(
        model_path,
        monitor="val_accuracy",
        save_best_only=True
    )
]

# ==============================
# TRAIN MODEL
# ==============================

print("\n🚀 Starting training...")
print("=" * 45)

history = model.fit(
    train_dataset,
    validation_data=validation_dataset,
    epochs=EPOCHS,
    callbacks=callbacks
)

# ==============================
# FINAL EVALUATION
# ==============================

print("\n📊 Evaluating model...")

loss, accuracy = model.evaluate(
    validation_dataset
)

print("\n" + "=" * 45)
print(f"✅ Validation Accuracy: {accuracy * 100:.2f}%")
print(f"✅ Validation Loss: {loss:.4f}")
print("=" * 45)

print("\n💾 Model saved at:")
print(model_path)

print("\n🎉 Training completed successfully!")