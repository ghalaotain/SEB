"use strict";

let stores = [];
let mapMode = "demo";

const elements = {
    app: document.querySelector("#mapApp"),
    search: document.querySelector("#storeSearch"),

    categoryFilters: document.querySelector(
        "#categoryFilters"
    ),

    storeCount: document.querySelector("#storeCount"),

    clearSelectionButton: document.querySelector(
        "#clearSelectionButton"
    ),

    storeList: document.querySelector("#storeList"),
    mapLocations: document.querySelector("#mapLocations"),
    mapStatus: document.querySelector("#mapStatus"),

    campaignNotice: document.querySelector(
        "#campaignNotice"
    ),

    campaignNoticeTitle: document.querySelector(
        "#campaignNoticeTitle"
    ),

    dismissCampaignNotice: document.querySelector(
        "#dismissCampaignNotice"
    ),

    storeDialog: document.querySelector("#storeDialog"),

    closeStoreDialog: document.querySelector(
        "#closeStoreDialog"
    ),

    storeDialogIcon: document.querySelector(
        "#storeDialogIcon"
    ),

    storeDialogCategory: document.querySelector(
        "#storeDialogCategory"
    ),

    storeDialogTitle: document.querySelector(
        "#storeDialogTitle"
    ),

    storeDialogDescription: document.querySelector(
        "#storeDialogDescription"
    ),

    storeDialogLocation: document.querySelector(
        "#storeDialogLocation"
    ),

    storeDialogHours: document.querySelector(
        "#storeDialogHours"
    ),

    showOnMapButton: document.querySelector(
        "#showOnMapButton"
    ),

    showQrButton: document.querySelector("#showQrButton"),

    qrDialog: document.querySelector("#qrDialog"),

    closeQrDialog: document.querySelector(
        "#closeQrDialog"
    ),

    qrDialogTitle: document.querySelector(
        "#qrDialogTitle"
    ),

    qrCode: document.querySelector("#qrCode"),

    qrLocationText: document.querySelector(
        "#qrLocationText"
    ),

    copyLocationButton: document.querySelector(
        "#copyLocationButton"
    ),

    message: document.querySelector("#mapMessage"),
};

const state = {
    activeCategory: "all",
    searchValue: "",
    selectedStore: null,
    messageTimer: null,
    currentLocationUrl: "",
};

function normalizeText(value) {
    return String(value || "")
        .toLowerCase()
        .replace(/[^\p{L}\p{N}]+/gu, " ")
        .trim();
}

function extractLocationParts(location) {
    const normalized = normalizeText(location);

    const hallMatch = normalized.match(
        /hall\s*([a-z])/i
    );

    const storeMatch = normalized.match(
        /store\s*0*(\d+)/i
    );

    return {
        hall: hallMatch
            ? hallMatch[1].toLowerCase()
            : "",

        storeNumber: storeMatch
            ? Number.parseInt(storeMatch[1], 10)
            : null,
    };
}

function locationsMatch(
    firstLocation,
    secondLocation
) {
    const first = extractLocationParts(
        firstLocation
    );

    const second = extractLocationParts(
        secondLocation
    );

    if (
        first.hall
        && second.hall
        && first.storeNumber !== null
        && second.storeNumber !== null
    ) {
        return (
            first.hall === second.hall
            && first.storeNumber
            === second.storeNumber
        );
    }

    return (
        normalizeText(firstLocation)
        === normalizeText(secondLocation)
    );
}

function createFallbackPosition(index) {
    const fallbackPositions = [
        {
            left: "4%",
            top: "7%",
            width: "25%",
            height: "24%",
        },
        {
            left: "62%",
            top: "7%",
            width: "32%",
            height: "24%",
        },
        {
            left: "62%",
            top: "58%",
            width: "32%",
            height: "25%",
        },
        {
            left: "4%",
            top: "58%",
            width: "25%",
            height: "25%",
        },
        {
            left: "34%",
            top: "7%",
            width: "17%",
            height: "24%",
        },
        {
            left: "34%",
            top: "58%",
            width: "17%",
            height: "25%",
        },
        {
            left: "54%",
            top: "34%",
            width: "18%",
            height: "16%",
        },
    ];

    return fallbackPositions[
        index % fallbackPositions.length
    ];
}

function createStoreIcon(name) {
    const words = String(name || "")
        .trim()
        .split(/\s+/)
        .filter(Boolean);

    if (!words.length) {
        return "S";
    }

    return words
        .slice(0, 2)
        .map((word) => word[0])
        .join("")
        .toUpperCase();
}

function formatCategory(category) {
    const value = String(
        category || "store"
    )
        .trim()
        .toLowerCase();

    return (
        value.charAt(0).toUpperCase()
        + value.slice(1)
    );
}

function normalizeStore(store, index) {
    const fallbackPosition =
        createFallbackPosition(index);

    const databasePosition =
        store.map_position || {};

    const validColor =
        /^#[0-9a-f]{6}$/i.test(
            store.color || ""
        )
            ? store.color
            : "#7565ff";

    return {
        id: Number(store.id),

        name:
            store.name
            || "Exhibition store",

        description:
            store.description
            || "Exhibition destination.",

        category:
            String(
                store.category || "services"
            ).toLowerCase(),

        categoryLabel: formatCategory(
            store.category
        ),

        location:
            store.map_location
            || "Exhibition hall",

        hours:
            store.opening_hours
            || "Hours unavailable",

        icon:
            store.icon
            || createStoreIcon(store.name),

        color: validColor,

        position: {
            left:
                databasePosition.left
                || fallbackPosition.left,

            top:
                databasePosition.top
                || fallbackPosition.top,

            width:
                databasePosition.width
                || fallbackPosition.width,

            height:
                databasePosition.height
                || fallbackPosition.height,
        },
    };
}

async function loadStores() {
    elements.mapStatus.textContent =
        "Loading map locations";

    const response = await fetch(
        "/api/stores",
        {
            method: "GET",
            headers: {
                Accept: "application/json",
            },
        }
    );

    let payload;

    try {
        payload = await response.json();
    } catch {
        throw new Error(
            "The store service returned "
            + "an invalid response."
        );
    }

    if (
        !response.ok
        || !payload.success
        || !Array.isArray(payload.stores)
    ) {
        throw new Error(
            payload?.error?.message
            || "Store locations could not be loaded."
        );
    }

    mapMode = payload.mode || "demo";

    stores = payload.stores.map(
        (store, index) => {
            return normalizeStore(
                store,
                index
            );
        }
    );
}

function getFilteredStores() {
    return stores.filter((store) => {
        const categoryMatches =
            state.activeCategory === "all"
            || store.category
            === state.activeCategory;

        const searchableText = normalizeText(
            [
                store.name,
                store.category,
                store.categoryLabel,
                store.location,
                store.description,
            ].join(" ")
        );

        const searchMatches =
            !state.searchValue
            || searchableText.includes(
                normalizeText(
                    state.searchValue
                )
            );

        return (
            categoryMatches
            && searchMatches
        );
    });
}

function createStoreCard(store) {
    const button =
        document.createElement("button");

    button.type = "button";
    button.className = "store-card";
    button.dataset.storeId = String(store.id);

    if (
        state.selectedStore
        && state.selectedStore.id === store.id
    ) {
        button.classList.add("is-selected");
    }

    const icon =
        document.createElement("span");

    icon.className = "store-card__icon";
    icon.textContent = store.icon;

    icon.style.setProperty(
        "--store-color",
        store.color
    );

    const content =
        document.createElement("span");

    content.className =
        "store-card__content";

    const name =
        document.createElement("strong");

    name.textContent = store.name;

    const category =
        document.createElement("span");

    category.textContent =
        store.categoryLabel;

    content.append(name, category);

    const location =
        document.createElement("span");

    location.className =
        "store-card__location";

    location.textContent = store.location;

    button.append(
        icon,
        content,
        location
    );

    button.addEventListener(
        "click",
        () => {
            selectStore(store, true);
        }
    );

    return button;
}

function createMapLocation(store) {
    const button =
        document.createElement("button");

    button.type = "button";
    button.className = "map-location";
    button.dataset.storeId = String(store.id);

    button.setAttribute(
        "aria-label",
        `${store.name}, ${store.location}`
    );

    button.style.left =
        store.position.left;

    button.style.top =
        store.position.top;

    button.style.width =
        store.position.width;

    button.style.height =
        store.position.height;

    button.style.setProperty(
        "--location-color",
        store.color
    );

    if (
        state.selectedStore
        && state.selectedStore.id === store.id
    ) {
        button.classList.add("is-selected");
    }

    const marker =
        document.createElement("span");

    marker.className =
        "map-location__marker";

    const category =
        document.createElement("small");

    category.textContent =
        store.categoryLabel;

    const name =
        document.createElement("strong");

    name.textContent = store.name;

    button.append(
        marker,
        category,
        name
    );

    button.addEventListener(
        "click",
        () => {
            selectStore(store, true);
        }
    );

    return button;
}

function renderStores() {
    const filteredStores =
        getFilteredStores();

    elements.storeList.replaceChildren();
    elements.mapLocations.replaceChildren();

    elements.storeCount.textContent =
        `${filteredStores.length} `
        + (
            filteredStores.length === 1
                ? "destination"
                : "destinations"
        );

    if (!filteredStores.length) {
        const emptyMessage =
            document.createElement("p");

        emptyMessage.className =
            "store-list__empty";

        emptyMessage.textContent =
            "No destinations match this search. "
            + "Try another store name or category.";

        elements.storeList.append(
            emptyMessage
        );

        elements.mapStatus.textContent =
            "No locations found";

        return;
    }

    filteredStores.forEach((store) => {
        elements.storeList.append(
            createStoreCard(store)
        );

        elements.mapLocations.append(
            createMapLocation(store)
        );
    });

    elements.mapStatus.textContent =
        mapMode === "demo"
            ? "Demo map ready"
            : "Map ready";
}

function updateCategoryButtons() {
    const buttons =
        elements.categoryFilters.querySelectorAll(
            "button[data-category]"
        );

    buttons.forEach((button) => {
        const isActive =
            button.dataset.category
            === state.activeCategory;

        button.classList.toggle(
            "is-active",
            isActive
        );

        button.setAttribute(
            "aria-pressed",
            String(isActive)
        );
    });
}

function openStoreDialog(store) {
    elements.storeDialogIcon.textContent =
        store.icon;

    elements.storeDialogIcon.style.background =
        store.color;

    elements.storeDialogCategory.textContent =
        store.categoryLabel;

    elements.storeDialogTitle.textContent =
        store.name;

    elements.storeDialogDescription.textContent =
        store.description;

    elements.storeDialogLocation.textContent =
        store.location;

    elements.storeDialogHours.textContent =
        store.hours;

    if (!elements.storeDialog.open) {
        elements.storeDialog.showModal();
    }
}

function selectStore(
    store,
    openDialog = false
) {
    state.selectedStore = store;

    elements.clearSelectionButton.hidden =
        false;

    renderStores();

    if (openDialog) {
        openStoreDialog(store);
    }
}

function clearSelection() {
    state.selectedStore = null;

    elements.clearSelectionButton.hidden =
        true;

    renderStores();
}

function focusSelectedLocation() {
    if (!state.selectedStore) {
        return;
    }

    state.activeCategory = "all";
    state.searchValue = "";
    elements.search.value = "";

    updateCategoryButtons();
    renderStores();

    const selectedLocation =
        elements.mapLocations.querySelector(
            `[data-store-id="${state.selectedStore.id}"]`
        );

    selectedLocation?.scrollIntoView({
        behavior: "smooth",
        block: "center",
    });

    selectedLocation?.focus();

    elements.storeDialog.close();
}

function createLocationUrl(store) {
    const url = new URL(
        "/display/map",
        window.location.origin
    );

    url.searchParams.set(
        "store",
        String(store.id)
    );

    url.searchParams.set(
        "location",
        store.location
    );

    return url.toString();
}

function showQrCode() {
    if (!state.selectedStore) {
        showMessage(
            "Select a destination first."
        );

        return;
    }

    const store = state.selectedStore;

    state.currentLocationUrl =
        createLocationUrl(store);

    elements.qrDialogTitle.textContent =
        `Directions to ${store.name}`;

    elements.qrLocationText.textContent =
        `${store.name} - ${store.location}`;

    elements.qrCode.replaceChildren();

    if (typeof window.QRCode !== "function") {
        showMessage(
            "QR library is unavailable. "
            + "Check the internet connection."
        );

        return;
    }

    new window.QRCode(
        elements.qrCode,
        {
            text: state.currentLocationUrl,
            width: 192,
            height: 192,
            colorDark: "#070713",
            colorLight: "#ffffff",
            correctLevel:
                window.QRCode.CorrectLevel.H,
        }
    );

    if (elements.storeDialog.open) {
        elements.storeDialog.close();
    }

    elements.qrDialog.showModal();
}

async function copyLocationLink() {
    if (!state.currentLocationUrl) {
        return;
    }

    try {
        await navigator.clipboard.writeText(
            state.currentLocationUrl
        );

        elements.copyLocationButton.textContent =
            "Location link copied";

        showMessage(
            "Location link copied."
        );

        window.setTimeout(() => {
            elements.copyLocationButton.textContent =
                "Copy location link";
        }, 1800);
    } catch {
        showMessage(
            "The link could not be copied. "
            + "Allow clipboard access "
            + "and try again."
        );
    }
}

function showMessage(message) {
    window.clearTimeout(
        state.messageTimer
    );

    elements.message.textContent =
        message;

    elements.message.hidden = false;

    state.messageTimer =
        window.setTimeout(() => {
            elements.message.hidden = true;
        }, 3000);
}

function closeDialogFromBackdrop(event) {
    const dialog = event.currentTarget;

    if (event.target === dialog) {
        dialog.close();
    }
}

function selectStoreFromUrl() {
    const parameters =
        new URLSearchParams(
            window.location.search
        );

    const storeId = Number.parseInt(
        parameters.get("store"),
        10
    );

    const requestedLocation =
        parameters.get("location") || "";

    const advertisementTitle =
        parameters.get("title") || "";

    let matchedStore = null;

    if (Number.isInteger(storeId)) {
        matchedStore = stores.find(
            (store) => {
                return store.id === storeId;
            }
        );
    }

    if (
        !matchedStore
        && requestedLocation
    ) {
        matchedStore = stores.find(
            (store) => {
                return locationsMatch(
                    store.location,
                    requestedLocation
                );
            }
        );
    }

    if (!matchedStore) {
        return;
    }

    state.selectedStore = matchedStore;

    elements.clearSelectionButton.hidden =
        false;

    elements.campaignNotice.hidden =
        false;

    elements.campaignNoticeTitle.textContent =
        advertisementTitle
            ? `${advertisementTitle} - ${matchedStore.name}`
            : `${matchedStore.name} - ${matchedStore.location}`;
}

function showMapLoadError(error) {
    console.error(error);

    elements.storeList.replaceChildren();
    elements.mapLocations.replaceChildren();

    const errorMessage =
        document.createElement("p");

    errorMessage.className =
        "store-list__empty";

    errorMessage.textContent =
        "Store locations could not be loaded. "
        + "Check that the Flask server is running, "
        + "then refresh the page.";

    elements.storeList.append(
        errorMessage
    );

    elements.storeCount.textContent =
        "0 destinations";

    elements.mapStatus.textContent =
        "Map unavailable";

    showMessage(
        error.message
        || "The map could not be loaded."
    );
}

function registerEvents() {
    elements.search.addEventListener(
        "input",
        (event) => {
            state.searchValue =
                event.target.value;

            renderStores();
        }
    );

    elements.categoryFilters.addEventListener(
        "click",
        (event) => {
            const button = event.target.closest(
                "button[data-category]"
            );

            if (!button) {
                return;
            }

            state.activeCategory =
                button.dataset.category;

            updateCategoryButtons();
            renderStores();
        }
    );

    elements.clearSelectionButton.addEventListener(
        "click",
        clearSelection
    );

    elements.closeStoreDialog.addEventListener(
        "click",
        () => {
            elements.storeDialog.close();
        }
    );

    elements.showOnMapButton.addEventListener(
        "click",
        focusSelectedLocation
    );

    elements.showQrButton.addEventListener(
        "click",
        showQrCode
    );

    elements.closeQrDialog.addEventListener(
        "click",
        () => {
            elements.qrDialog.close();
        }
    );

    elements.copyLocationButton.addEventListener(
        "click",
        copyLocationLink
    );

    elements.dismissCampaignNotice.addEventListener(
        "click",
        () => {
            elements.campaignNotice.hidden =
                true;
        }
    );

    elements.storeDialog.addEventListener(
        "click",
        closeDialogFromBackdrop
    );

    elements.qrDialog.addEventListener(
        "click",
        closeDialogFromBackdrop
    );
}

async function initializeMap() {
    registerEvents();
    updateCategoryButtons();

    try {
        await loadStores();

        selectStoreFromUrl();
        renderStores();

        if (state.selectedStore) {
            window.setTimeout(() => {
                const selectedLocation =
                    elements.mapLocations.querySelector(
                        `[data-store-id="${state.selectedStore.id}"]`
                    );

                selectedLocation?.focus();
            }, 150);
        }
    } catch (error) {
        showMapLoadError(error);
    }
}

initializeMap();