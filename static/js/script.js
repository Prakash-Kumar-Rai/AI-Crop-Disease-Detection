// Tab Switching
function switchTab(type) {
    const tabFile = document.getElementById("tab-file");
    const tabUrl = document.getElementById("tab-url");
    const filePane = document.getElementById("file-input-pane");
    const urlPane = document.getElementById("url-input-pane");
    const sourceType = document.getElementById("source-type");
    const previewContainer = document.getElementById("preview-container");
    const imagePreview = document.getElementById("image-preview");

    if (type === "file") {
        tabFile.classList.add("active");
        tabUrl.classList.remove("active");
        filePane.style.display = "block";
        urlPane.style.display = "none";
        sourceType.value = "file";
    } else {
        tabUrl.classList.add("active");
        tabFile.classList.remove("active");
        urlPane.style.display = "block";
        filePane.style.display = "none";
        sourceType.value = "url";
    }
}

// Local File Upload Preview
const imageInput = document.getElementById("image");
const previewContainer = document.getElementById("preview-container");
const imagePreview = document.getElementById("image-preview");

if (imageInput) {
    imageInput.addEventListener("change", function () {
        const file = this.files[0];

        if (!file) {
            previewContainer.style.display = "none";
            imagePreview.src = "";
            return;
        }

        if (!file.type.startsWith("image/")) {
            alert("Please select a valid image file (JPG, PNG, WEBP).");
            this.value = "";
            previewContainer.style.display = "none";
            return;
        }

        const imageURL = URL.createObjectURL(file);
        imagePreview.src = imageURL;
        previewContainer.style.display = "block";

        imagePreview.onload = function () {
            URL.revokeObjectURL(imageURL);
        };
    });
}

// Internet URL Preview
function previewUrlImage() {
    const urlInput = document.getElementById("image-url-input");
    const url = urlInput ? urlInput.value.trim() : "";

    if (!url) {
        alert("Please paste an image URL first.");
        return;
    }

    if (!url.startsWith("http://") && !url.startsWith("https://")) {
        alert("Please enter a valid URL starting with http:// or https://");
        return;
    }

    // Attempt to load preview
    const tempImg = new Image();
    tempImg.onload = function () {
        imagePreview.src = url;
        previewContainer.style.display = "block";
    };
    tempImg.onerror = function () {
        alert("Unable to preview image from this URL. Please verify the URL points directly to an image.");
    };
    tempImg.src = url;
}

// Form Submission Loading State
const predictionForm = document.getElementById("prediction-form");
const detectBtn = document.getElementById("detect-btn");

if (predictionForm && detectBtn) {
    predictionForm.addEventListener("submit", function (e) {
        const sourceType = document.getElementById("source-type").value;
        const fileInput = document.getElementById("image");
        const urlInput = document.getElementById("image-url-input");

        if (sourceType === "file" && (!fileInput.files || fileInput.files.length === 0)) {
            alert("Please choose a crop leaf image file first.");
            e.preventDefault();
            return;
        }

        if (sourceType === "url" && (!urlInput.value || urlInput.value.trim() === "")) {
            alert("Please paste an image URL from the internet.");
            e.preventDefault();
            return;
        }

        detectBtn.disabled = true;
        detectBtn.innerHTML = "⏳ Analyzing & Fetching Live Agronomic Advice...";
        detectBtn.style.opacity = "0.75";
    });
}

// Reset / Try Another Image
function tryAnotherImage() {
    window.location.href = "/";
}