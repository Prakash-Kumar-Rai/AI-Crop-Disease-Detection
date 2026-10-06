/**
 * AgriVision AI — Client JavaScript Application
 * Handles Input Modes, Live Camera Capture, Drag-and-Drop, Demo Samples,
 * Interactive Prescription Tabs, and Modal Explorer.
 */

let cameraStream = null;
let currentFacingMode = "environment"; // Prefer rear camera on mobile phones

// ==========================================================================
// INPUT MODE SWITCHER
// ==========================================================================

function setMode(mode) {
    const modes = ["file", "camera", "url", "sample"];
    const sourceTypeInput = document.getElementById("source-type");

    modes.forEach(m => {
        const tab = document.getElementById(`tab-${m}`);
        const pane = document.getElementById(`pane-${m}`);
        if (tab && pane) {
            if (m === mode) {
                tab.classList.add("active");
                pane.style.display = "block";
            } else {
                tab.classList.remove("active");
                pane.style.display = "none";
            }
        }
    });

    if (sourceTypeInput) {
        sourceTypeInput.value = mode;
    }

    // Stop camera stream if navigating away from camera tab
    if (mode !== "camera" && cameraStream) {
        stopCamera();
    }
}

// ==========================================================================
// FILE INPUT & DRAG AND DROP
// ==========================================================================

const fileInput = document.getElementById("file-input");
const dropzone = document.getElementById("dropzone");
const previewPanel = document.getElementById("preview-panel");
const imagePreview = document.getElementById("image-preview");

if (fileInput) {
    fileInput.addEventListener("change", function () {
        const file = this.files[0];
        handleSelectedFile(file);
    });
}

if (dropzone) {
    ["dragenter", "dragover"].forEach(eventName => {
        dropzone.addEventListener(eventName, e => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.style.borderColor = "var(--accent)";
            dropzone.style.background = "rgba(52, 211, 153, 0.12)";
        });
    });

    ["dragleave", "drop"].forEach(eventName => {
        dropzone.addEventListener(eventName, e => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.style.borderColor = "rgba(52, 211, 153, 0.4)";
            dropzone.style.background = "rgba(0, 0, 0, 0.16)";
        });
    });

    dropzone.addEventListener("drop", e => {
        const dt = e.dataTransfer;
        const file = dt.files[0];
        if (file && fileInput) {
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            fileInput.files = dataTransfer.files;
            handleSelectedFile(file);
        }
    });
}

function handleSelectedFile(file) {
    if (!file) {
        clearSelectedImage();
        return;
    }

    if (!file.type.startsWith("image/")) {
        alert("Please select a valid image file (JPG, PNG, WEBP).");
        clearSelectedImage();
        return;
    }

    const objectUrl = URL.createObjectURL(file);
    imagePreview.src = objectUrl;
    previewPanel.style.display = "block";

    imagePreview.onload = () => URL.revokeObjectURL(objectUrl);
}

// ==========================================================================
// LIVE WEBCAM & SMARTPHONE CAMERA CAPTURE
// ==========================================================================

async function initCamera() {
    const videoElem = document.getElementById("camera-stream");
    const btnStart = document.getElementById("btn-start-camera");
    const btnSnap = document.getElementById("btn-snap-photo");
    const btnSwitch = document.getElementById("btn-switch-camera");

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        alert("Camera access is not supported by your browser or requires HTTPS.");
        return;
    }

    try {
        if (cameraStream) {
            stopCamera();
        }

        const constraints = {
            video: {
                facingMode: currentFacingMode,
                width: { ideal: 1280 },
                height: { ideal: 720 }
            },
            audio: false
        };

        cameraStream = await navigator.mediaDevices.getUserMedia(constraints);
        videoElem.srcObject = cameraStream;

        btnStart.style.display = "none";
        btnSnap.style.display = "inline-block";
        btnSwitch.style.display = "inline-block";
    } catch (err) {
        console.error("Camera access error:", err);
        alert("Unable to access camera: " + (err.message || "Permission denied"));
    }
}

function stopCamera() {
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
    }
    const videoElem = document.getElementById("camera-stream");
    if (videoElem) {
        videoElem.srcObject = null;
    }
    const btnStart = document.getElementById("btn-start-camera");
    const btnSnap = document.getElementById("btn-snap-photo");
    const btnSwitch = document.getElementById("btn-switch-camera");

    if (btnStart) btnStart.style.display = "inline-block";
    if (btnSnap) btnSnap.style.display = "none";
    if (btnSwitch) btnSwitch.style.display = "none";
}

function switchCameraFacing() {
    currentFacingMode = currentFacingMode === "environment" ? "user" : "environment";
    initCamera();
}

function captureSnapshot() {
    const videoElem = document.getElementById("camera-stream");
    const canvasElem = document.getElementById("camera-canvas");
    const cameraInput = document.getElementById("camera-image-input");

    if (!videoElem || !canvasElem || !videoElem.videoWidth) {
        alert("Camera stream is not ready.");
        return;
    }

    canvasElem.width = videoElem.videoWidth;
    canvasElem.height = videoElem.videoHeight;
    const ctx = canvasElem.getContext("2d");
    ctx.drawImage(videoElem, 0, 0, canvasElem.width, canvasElem.height);

    const dataUrl = canvasElem.toDataURL("image/jpeg", 0.92);
    cameraInput.value = dataUrl;

    imagePreview.src = dataUrl;
    previewPanel.style.display = "block";

    stopCamera();
}

// ==========================================================================
// INTERNET IMAGE URL PREVIEW
// ==========================================================================

function loadUrlPreview() {
    const urlInput = document.getElementById("image-url-input");
    const url = urlInput ? urlInput.value.trim() : "";

    if (!url) {
        alert("Please paste an image URL first.");
        return;
    }

    if (!url.startsWith("http://") && !url.startsWith("https://")) {
        alert("The image URL must start with http:// or https://");
        return;
    }

    const testImg = new Image();
    testImg.onload = function () {
        imagePreview.src = url;
        previewPanel.style.display = "block";
    };
    testImg.onerror = function () {
        alert("Could not load preview. Please ensure the link points directly to an image file (JPG, PNG, WEBP).");
    };
    testImg.src = url;
}

// ==========================================================================
// 1-CLICK DEMO QUICK SAMPLES
// ==========================================================================

function selectDemoSample(sampleFilename, cropKey, sampleTitle) {
    const sampleInput = document.getElementById("sample-image-input");
    const cropSelect = document.getElementById("target_crop");
    const sourceType = document.getElementById("source-type");

    if (sampleInput) sampleInput.value = sampleFilename;
    if (sourceType) sourceType.value = "sample";
    if (cropSelect && cropKey) cropSelect.value = cropKey;

    imagePreview.src = `/static/samples/${sampleFilename}`;
    previewPanel.style.display = "block";

    // Scroll to submit button smoothly
    const submitBtn = document.getElementById("analyze-btn");
    if (submitBtn) {
        submitBtn.scrollIntoView({ behavior: "smooth", block: "center" });
    }
}

// ==========================================================================
// CLEAR PREVIEW
// ==========================================================================

function clearSelectedImage() {
    if (fileInput) fileInput.value = "";
    const cameraInput = document.getElementById("camera-image-input");
    if (cameraInput) cameraInput.value = "";
    const sampleInput = document.getElementById("sample-image-input");
    if (sampleInput) sampleInput.value = "";
    const urlInput = document.getElementById("image-url-input");
    if (urlInput) urlInput.value = "";

    if (imagePreview) imagePreview.src = "";
    if (previewPanel) previewPanel.style.display = "none";
}

// ==========================================================================
// FORM SUBMISSION & LOADING STATE
// ==========================================================================

const mainForm = document.getElementById("main-prediction-form");
const analyzeBtn = document.getElementById("analyze-btn");

if (mainForm && analyzeBtn) {
    mainForm.addEventListener("submit", function (e) {
        const sourceType = document.getElementById("source-type").value;

        if (sourceType === "file") {
            if (!fileInput.files || fileInput.files.length === 0) {
                alert("Please select or drop a crop leaf image first.");
                e.preventDefault();
                return;
            }
        } else if (sourceType === "camera") {
            const camData = document.getElementById("camera-image-input").value;
            if (!camData) {
                alert("Please capture a photo using the camera first.");
                e.preventDefault();
                return;
            }
        } else if (sourceType === "url") {
            const urlData = document.getElementById("image-url-input").value.trim();
            if (!urlData) {
                alert("Please paste an image URL first.");
                e.preventDefault();
                return;
            }
        } else if (sourceType === "sample") {
            const sampleData = document.getElementById("sample-image-input").value;
            if (!sampleData) {
                alert("Please select a sample crop image first.");
                e.preventDefault();
                return;
            }
        }

        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = "⏳ Screening Plant & Analyzing Pathology...";
        analyzeBtn.style.opacity = "0.75";
    });
}

// ==========================================================================
// INTERACTIVE AGRONOMIC PRESCRIPTION TABS
// ==========================================================================

function switchPrescTab(tabKey, btnElem) {
    // Deactivate all tab buttons
    document.querySelectorAll(".presc-tab").forEach(tab => tab.classList.remove("active"));
    // Deactivate all panes
    document.querySelectorAll(".presc-pane").forEach(pane => pane.classList.remove("active"));

    if (btnElem) btnElem.classList.add("active");
    const targetPane = document.getElementById(`pane-${tabKey}`);
    if (targetPane) targetPane.classList.add("active");
}

// ==========================================================================
// RESET TO UPLOAD VIEW
// ==========================================================================

function resetToUpload() {
    window.location.href = "/";
}

// ==========================================================================
// SUPPORTED CROPS MODAL
// ==========================================================================

function openCropsModal() {
    const modal = document.getElementById("crops-modal");
    if (modal) modal.classList.add("open");
}

function closeCropsModal(event) {
    if (event && event.target.id !== "crops-modal" && !event.target.classList.contains("modal-close-btn")) {
        return;
    }
    const modal = document.getElementById("crops-modal");
    if (modal) modal.classList.remove("open");
}