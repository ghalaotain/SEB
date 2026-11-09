"use strict";

const elements = {
    app: document.querySelector("#displayApp"),
    modeBadge: document.querySelector("#modeBadge"),

    carouselView: document.querySelector("#carouselView"),
    cameraView: document.querySelector("#cameraView"),
    resultView: document.querySelector("#resultView"),

    adCategory: document.querySelector("#adCategory"),
    adCounter: document.querySelector("#adCounter"),
    adTitle: document.querySelector("#adTitle"),
    adDescription: document.querySelector("#adDescription"),
    adLocation: document.querySelector("#adLocation"),
    carouselDots: document.querySelector("#carouselDots"),

    visualNumber: document.querySelector("#visualNumber"),
    visualCategory: document.querySelector("#visualCategory"),
    visualTitle: document.querySelector("#visualTitle"),
    campaignVisual: document.querySelector("#campaignVisual"),
    campaignImage: document.querySelector("#campaignImage"),

    startButton: document.querySelector("#startButton"),
    cancelAnalysisButton: document.querySelector(
        "#cancelAnalysisButton"
    ),

    consentDialog: document.querySelector("#consentDialog"),
    consentContinueButton: document.querySelector(
        "#consentContinueButton"
    ),
    consentCancelButton: document.querySelector(
        "#consentCancelButton"
    ),

    cameraVideo: document.querySelector("#cameraVideo"),
    captureCanvas: document.querySelector("#captureCanvas"),
    cameraStatus: document.querySelector("#cameraStatus"),

    resultModeBadge: document.querySelector("#resultModeBadge"),
    resultTitle: document.querySelector("#resultTitle"),
    resultDescription: document.querySelector(
        "#resultDescription"
    ),
    resultAgeGroup: document.querySelector("#resultAgeGroup"),
    resultGender: document.querySelector("#resultGender"),
    resultCategory: document.querySelector("#resultCategory"),
    resultLocation: document.querySelector("#resultLocation"),
    resultVisualCategory: document.querySelector(
        "#resultVisualCategory"
    ),
    resultVisualTitle: document.querySelector(
        "#resultVisualTitle"
    ),
    resultVisual: document.querySelector("#resultVisual"),
    resultImage: document.querySelector("#resultImage"),
    resultMapLink: document.querySelector("#resultMapLink"),
    resultQrLink: document.querySelector("#resultQrLink"),
    returnButton: document.querySelector("#returnButton"),
    returnCountdown: document.querySelector("#returnCountdown"),

    errorMessage: document.querySelector("#errorMessage"),
    errorText: document.querySelector("#errorText"),
    dismissErrorButton: document.querySelector(
        "#dismissErrorButton"
    ),

    systemStatus: document.querySelector("#systemStatus"),
};

const allowedThemes = new Set([
    "violet",
    "cyan",
    "pink",
    "yellow",
]);

const state = {
    advertisements: [],
    activeIndex: 0,
    carouselTimer: null,
    mediaStream: null,
    returnTimer: null,
    countdownTimer: null,
    isAnalyzing: false,
};

const CAROUSEL_INTERVAL = 7000;
const RESULT_DURATION = 15;

function wait(milliseconds) {
    return new Promise((resolve) => {
        window.setTimeout(resolve, milliseconds);
    });
}

function setTheme(theme) {
    const safeTheme = allowedThemes.has(theme)
        ? theme
        : "violet";

    elements.app.dataset.theme = safeTheme;
}

function setAdvertisementImage(container, image, imagePath) {
    if (imagePath) {
        image.src = imagePath;
        image.hidden = false;
        container.classList.add("has-image");
        return;
    }

    image.removeAttribute("src");
    image.hidden = true;
    container.classList.remove("has-image");
}

function setView(viewName) {
    elements.carouselView.hidden = viewName !== "carousel";
    elements.cameraView.hidden = viewName !== "camera";
    elements.resultView.hidden = viewName !== "result";
}

function setSystemStatus(message) {
    elements.systemStatus.textContent = message;
}

function showError(message) {
    elements.errorText.textContent = message;
    elements.errorMessage.hidden = false;
}

function hideError() {
    elements.errorMessage.hidden = true;
    elements.errorText.textContent = "";
}

function stopCamera() {
    if (state.mediaStream) {
        for (const track of state.mediaStream.getTracks()) {
            track.stop();
        }
    }

    state.mediaStream = null;
    elements.cameraVideo.srcObject = null;
}

function clearTimers() {
    if (state.returnTimer) {
        window.clearTimeout(state.returnTimer);
    }

    if (state.countdownTimer) {
        window.clearInterval(state.countdownTimer);
    }

    state.returnTimer = null;
    state.countdownTimer = null;
}

function stopCarousel() {
    if (state.carouselTimer) {
        window.clearInterval(state.carouselTimer);
    }

    state.carouselTimer = null;
}

function startCarousel() {
    stopCarousel();

    if (state.advertisements.length < 2) {
        return;
    }

    state.carouselTimer = window.setInterval(() => {
        const nextIndex =
            (state.activeIndex + 1)
            % state.advertisements.length;

        renderAdvertisement(nextIndex);
    }, CAROUSEL_INTERVAL);
}

function createCarouselDots() {
    elements.carouselDots.replaceChildren();

    state.advertisements.forEach((advertisement, index) => {
        const button = document.createElement("button");

        button.type = "button";
        button.setAttribute(
            "aria-label",
            `Show advertisement ${index + 1}`
        );

        button.addEventListener("click", () => {
            renderAdvertisement(index);
            startCarousel();
        });

        elements.carouselDots.append(button);
    });
}

function renderAdvertisement(index) {
    const advertisement = state.advertisements[index];

    if (!advertisement) {
        return;
    }

    state.activeIndex = index;

    const number = String(index + 1).padStart(2, "0");
    const total = String(
        state.advertisements.length
    ).padStart(2, "0");

    elements.adCategory.textContent =
        advertisement.category || "Campaign";

    elements.adCounter.textContent = `${number} / ${total}`;
    elements.adTitle.textContent = advertisement.title;
    elements.adDescription.textContent =
        advertisement.description || "";

    elements.adLocation.textContent =
        advertisement.map_location || "Exhibition hall";

    elements.visualNumber.textContent = number;
    elements.visualCategory.textContent =
        advertisement.category || "Campaign";

    elements.visualTitle.textContent =
        advertisement.title;

    setAdvertisementImage(
        elements.campaignVisual,
        elements.campaignImage,
        advertisement.image_url || advertisement.image_path
    );

    setTheme(advertisement.theme);

    const dots = elements.carouselDots.querySelectorAll(
        "button"
    );

    dots.forEach((dot, dotIndex) => {
        dot.classList.toggle(
            "is-active",
            dotIndex === index
        );
    });
}

async function loadAdvertisements() {
    setSystemStatus("Loading campaigns");

    try {
        const response = await fetch("/api/ads", {
            headers: {
                Accept: "application/json",
            },
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(
                data.error?.message
                || "Advertisements could not be loaded."
            );
        }

        state.advertisements = data.ads || [];

        if (data.mode === "demo") {
            elements.modeBadge.hidden = false;
        }

        if (state.advertisements.length === 0) {
            throw new Error(
                "No active advertisements are available."
            );
        }

        createCarouselDots();
        renderAdvertisement(0);
        startCarousel();

        setSystemStatus("System ready");
    }
    catch (error) {
        setSystemStatus("Campaigns unavailable");
        showError(error.message);
    }
}

function openConsentDialog() {
    hideError();

    if (
        typeof elements.consentDialog.showModal
        === "function"
    ) {
        elements.consentDialog.showModal();
    }
    else {
        showError(
            "This browser does not support the consent dialog."
        );
    }
}

function closeConsentDialog() {
    if (elements.consentDialog.open) {
        elements.consentDialog.close();
    }
}

async function requestCamera() {
    if (
        !navigator.mediaDevices
        || !navigator.mediaDevices.getUserMedia
    ) {
        throw new Error(
            "Camera access is not supported by this browser."
        );
    }

    return navigator.mediaDevices.getUserMedia({
        audio: false,
        video: {
            facingMode: "user",
            width: {
                ideal: 1280,
            },
            height: {
                ideal: 720,
            },
        },
    });
}

function captureFrame() {
    const video = elements.cameraVideo;
    const canvas = elements.captureCanvas;

    const width = video.videoWidth || 640;
    const height = video.videoHeight || 480;

    canvas.width = width;
    canvas.height = height;

    const context = canvas.getContext("2d");

    if (!context) {
        throw new Error(
            "The camera frame could not be prepared."
        );
    }

    context.drawImage(
        video,
        0,
        0,
        width,
        height
    );

    return canvas.toDataURL(
        "image/jpeg",
        0.82
    );
}

async function sendFrameForAnalysis(imageData) {
    const response = await fetch("/api/analyze", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
        },
        body: JSON.stringify({
            image: imageData,
        }),
    });

    const data = await response.json();

    if (!response.ok || !data.success) {
        throw new Error(
            data.error?.message
            || "Visitor analysis could not be completed."
        );
    }

    return data;
}

async function beginAnalysis() {
    if (state.isAnalyzing) {
        return;
    }

    state.isAnalyzing = true;
    closeConsentDialog();
    stopCarousel();
    hideError();

    setView("camera");
    setSystemStatus("Camera starting");
    elements.cameraStatus.textContent =
        "Allow camera access when prompted.";

    try {
        state.mediaStream = await requestCamera();

        elements.cameraVideo.srcObject =
            state.mediaStream;

        await elements.cameraVideo.play();

        elements.cameraStatus.textContent =
            "Keep your face inside the guide.";

        setSystemStatus("Preparing frame");

        await wait(1800);

        elements.cameraStatus.textContent =
            "Capturing one temporary frame…";

        const imageData = captureFrame();

        stopCamera();

        elements.cameraStatus.textContent =
            "Analyzing demographic attributes…";

        setSystemStatus("Analysis in progress");

        await wait(700);

        const result = await sendFrameForAnalysis(
            imageData
        );

        displayResult(result);
    }
    catch (error) {
        stopCamera();

        let message = error.message;

        if (
            error.name === "NotAllowedError"
            || error.name === "PermissionDeniedError"
        ) {
            message = (
                "Camera permission was denied. "
                + "Allow camera access and try again."
            );
        }
        else if (
            error.name === "NotFoundError"
            || error.name === "DevicesNotFoundError"
        ) {
            message = (
                "No camera was found on this device."
            );
        }

        showError(message);
        returnToCarousel();
    }
    finally {
        state.isAnalyzing = false;
    }
}

function displayResult(result) {
    clearTimers();
    stopCamera();

    const analysis = result.analysis || {};
    const advertisement = result.advertisement || {};

    elements.resultTitle.textContent =
        advertisement.title
        || "Selected advertisement";

    elements.resultDescription.textContent =
        advertisement.description || "";

    elements.resultAgeGroup.textContent =
        analysis.age_group || "Unavailable";

    elements.resultGender.textContent =
        analysis.gender || "Unavailable";

    elements.resultCategory.textContent =
        advertisement.category || "General";

    elements.resultLocation.textContent =
        advertisement.map_location
        || "Exhibition hall";

    elements.resultVisualCategory.textContent =
        advertisement.category || "Campaign";

    elements.resultVisualTitle.textContent =
        advertisement.title
        || "Selected advertisement";

    setAdvertisementImage(
        elements.resultVisual,
        elements.resultImage,
        advertisement.image_url || advertisement.image_path
    );

    const theme = advertisement.theme || "violet";
    setTheme(theme);

    const mapParameters = new URLSearchParams({
        ad_id: String(advertisement.id || ""),
        title: advertisement.title || "",
        location: advertisement.map_location || "",
    });

    elements.resultMapLink.href =
        `/display/map?${mapParameters.toString()}`;

    if (advertisement.qr_code_url) {
        elements.resultQrLink.href =
            advertisement.qr_code_url;

        elements.resultQrLink.hidden = false;
    }
    else {
        elements.resultQrLink.hidden = true;
    }

    if (result.mode === "demo") {
        elements.resultModeBadge.textContent =
            "Simulated result · Demo mode";
    }
    else {
        elements.resultModeBadge.textContent =
            "Live demographic estimate";
    }

    setView("result");
    setSystemStatus("Advertisement selected");

    beginReturnCountdown();
}

function beginReturnCountdown() {
    let remainingSeconds = RESULT_DURATION;

    elements.returnCountdown.textContent =
        String(remainingSeconds);

    state.countdownTimer = window.setInterval(() => {
        remainingSeconds -= 1;

        elements.returnCountdown.textContent =
            String(Math.max(remainingSeconds, 0));
    }, 1000);

    state.returnTimer = window.setTimeout(() => {
        returnToCarousel();
    }, RESULT_DURATION * 1000);
}

function returnToCarousel() {
    clearTimers();
    stopCamera();

    state.isAnalyzing = false;

    setView("carousel");
    setSystemStatus("System ready");

    startCarousel();
}

elements.startButton.addEventListener(
    "click",
    openConsentDialog
);

elements.consentContinueButton.addEventListener(
    "click",
    beginAnalysis
);

elements.consentCancelButton.addEventListener(
    "click",
    closeConsentDialog
);

elements.cancelAnalysisButton.addEventListener(
    "click",
    returnToCarousel
);

elements.returnButton.addEventListener(
    "click",
    returnToCarousel
);

elements.dismissErrorButton.addEventListener(
    "click",
    hideError
);

elements.consentDialog.addEventListener(
    "cancel",
    () => {
        closeConsentDialog();
    }
);

document.addEventListener(
    "visibilitychange",
    () => {
        if (document.hidden) {
            stopCamera();
        }
    }
);

window.addEventListener(
    "beforeunload",
    stopCamera
);

loadAdvertisements();
