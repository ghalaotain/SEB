"use strict";

const elements = {
    totalVisitors: document.querySelector("#totalVisitors"),
    todayVisitors: document.querySelector("#todayVisitors"),
    maleVisitors: document.querySelector("#maleVisitors"),
    femaleVisitors: document.querySelector("#femaleVisitors"),
    activeAdvertisements: document.querySelector("#activeAdvertisements"),
    totalAdvertisementViews: document.querySelector("#totalAdvertisementViews"),
    mode: document.querySelector("#dashboardMode"),
    refreshButton: document.querySelector("#refreshDashboard"),
    lastUpdated: document.querySelector("#lastUpdated"),
    error: document.querySelector("#dashboardError"),
    errorText: document.querySelector("#dashboardErrorText"),
    advertisementCount: document.querySelector("#advertisementCount"),
    advertisementTableBody: document.querySelector("#advertisementTableBody"),
    addButton: document.querySelector("#addAdvertisementButton"),
    search: document.querySelector("#advertisementSearch"),
    statusFilter: document.querySelector("#advertisementStatusFilter"),
    dialog: document.querySelector("#advertisementDialog"),
    dialogTitle: document.querySelector("#advertisementDialogTitle"),
    form: document.querySelector("#advertisementForm"),
    formError: document.querySelector("#advertisementFormError"),
    saveButton: document.querySelector("#saveAdvertisementButton"),
    closeDialog: document.querySelector("#closeAdvertisementDialog"),
    cancelButton: document.querySelector("#cancelAdvertisementButton"),
    deleteDialog: document.querySelector("#deleteAdvertisementDialog"),
    deleteName: document.querySelector("#deleteAdvertisementName"),
    cancelDelete: document.querySelector("#cancelDeleteAdvertisement"),
    confirmDelete: document.querySelector("#confirmDeleteAdvertisement"),
    toast: document.querySelector("#adminToast"),
    id: document.querySelector("#advertisementId"),
    title: document.querySelector("#advertisementTitle"),
    description: document.querySelector("#advertisementDescription"),
    category: document.querySelector("#advertisementCategory"),
    gender: document.querySelector("#advertisementGender"),
    ageMin: document.querySelector("#advertisementAgeMin"),
    ageMax: document.querySelector("#advertisementAgeMax"),
    theme: document.querySelector("#advertisementTheme"),
    store: document.querySelector("#advertisementStore"),
    imagePath: document.querySelector("#advertisementImagePath"),
    imageFile: document.querySelector("#advertisementImageFile"),
    imagePreview: document.querySelector("#advertisementImagePreview"),
    imagePlaceholder: document.querySelector("#advertisementImagePlaceholder"),
    qrUrl: document.querySelector("#advertisementQrUrl"),
    mapLocation: document.querySelector("#advertisementMapLocation"),
    isActive: document.querySelector("#advertisementIsActive"),
};

const state = {
    advertisements: [],
    stores: [],
    pendingDeleteId: null,
    searchTimer: null,
    toastTimer: null,
    previewObjectUrl: null,
};

const charts = {
    daily: null,
    gender: null,
    age: null,
    advertisements: null,
};

const numberFormatter = new Intl.NumberFormat("en-US");

function formatNumber(value) {
    return numberFormatter.format(Number(value) || 0);
}

function csrfToken() {
    return document.querySelector('meta[name="csrf-token"]')?.content || "";
}

async function fetchJson(url, options = {}) {
    const method = options.method || "GET";
    const headers = {
        Accept: "application/json",
        ...(options.headers || {}),
    };

    if (method !== "GET" && method !== "HEAD") {
        headers["Content-Type"] = "application/json";
        headers["X-CSRFToken"] = csrfToken();
    }

    const response = await fetch(url, {
        ...options,
        method,
        headers,
        credentials: "same-origin",
    });

    if (response.redirected || response.status === 401) {
        window.location.assign("/admin/login");
        throw new Error("Administrator session expired.");
    }

    let payload;

    try {
        payload = await response.json();
    } catch {
        throw new Error("The server returned an invalid response.");
    }

    if (!response.ok || !payload.success) {
        throw new Error(
            payload?.error?.message
            || "The requested operation could not be completed."
        );
    }

    return payload;
}

function destroyChart(name) {
    if (charts[name]) {
        charts[name].destroy();
        charts[name] = null;
    }
}

function configureChartDefaults() {
    if (typeof window.Chart !== "function") {
        throw new Error("Chart.js could not be loaded.");
    }

    window.Chart.defaults.color = "#aaa9c1";
    window.Chart.defaults.font.family = '"Outfit", "Segoe UI", sans-serif';
    window.Chart.defaults.borderColor = "rgba(255, 255, 255, 0.08)";
}

function renderSummary(statistics) {
    const summary = statistics.summary;

    elements.totalVisitors.textContent = formatNumber(summary.total_visitors);
    elements.todayVisitors.textContent = formatNumber(summary.today_visitors);
    elements.maleVisitors.textContent = formatNumber(summary.male_count);
    elements.femaleVisitors.textContent = formatNumber(summary.female_count);
    elements.activeAdvertisements.textContent = formatNumber(summary.active_advertisements);
    elements.totalAdvertisementViews.textContent = formatNumber(summary.total_ad_views);
    elements.mode.textContent = statistics.mode === "demo" ? "Demo mode" : "Live mode";

    const generatedDate = new Date(statistics.generated_at);
    elements.lastUpdated.textContent = Number.isNaN(generatedDate.getTime())
        ? "Updated now"
        : `Updated ${generatedDate.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
        })}`;
}

function renderDailyChart(records) {
    destroyChart("daily");
    const labels = records.length
        ? records.map((record) => record.date)
        : ["No activity"];
    const values = records.length
        ? records.map((record) => record.total_visitors)
        : [0];
    const context = document.querySelector("#dailyVisitorsChart").getContext("2d");
    const gradient = context.createLinearGradient(0, 0, 0, 340);

    gradient.addColorStop(0, "rgba(117, 101, 255, 0.38)");
    gradient.addColorStop(1, "rgba(117, 101, 255, 0)");

    charts.daily = new window.Chart(context, {
        type: "line",
        data: {
            labels,
            datasets: [{
                label: "Visitors",
                data: values,
                borderColor: "#8f82ff",
                backgroundColor: gradient,
                fill: true,
                borderWidth: 3,
                pointRadius: 3,
                pointHoverRadius: 6,
                pointBackgroundColor: "#65e5d8",
                tension: 0.35,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { intersect: false, mode: "index" },
            plugins: { legend: { display: false } },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { precision: 0 },
                    grid: { color: "rgba(255,255,255,0.06)" },
                },
                x: { grid: { display: false } },
            },
        },
    });
}

function renderGenderChart(genderData) {
    destroyChart("gender");
    charts.gender = new window.Chart(document.querySelector("#genderChart"), {
        type: "doughnut",
        data: {
            labels: genderData.map((item) => item.label),
            datasets: [{
                data: genderData.map((item) => item.value),
                backgroundColor: ["#7565ff", "#ed72c5", "#74738a"],
                borderWidth: 0,
                hoverOffset: 5,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: "72%",
            plugins: {
                legend: {
                    position: "bottom",
                    labels: { usePointStyle: true, padding: 18 },
                },
            },
        },
    });
}

function renderAgeChart(ageGroups) {
    destroyChart("age");
    charts.age = new window.Chart(document.querySelector("#ageGroupsChart"), {
        type: "bar",
        data: {
            labels: ageGroups.map((item) => item.label),
            datasets: [{
                label: "Visitors",
                data: ageGroups.map((item) => item.value),
                backgroundColor: ["#7565ff", "#8f82ff", "#65e5d8", "#ed72c5", "#f5c86b"],
                borderRadius: 7,
                borderSkipped: false,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { precision: 0 },
                    grid: { color: "rgba(255,255,255,0.06)" },
                },
                x: { grid: { display: false } },
            },
        },
    });
}

function renderAdvertisementChart(advertisements) {
    destroyChart("advertisements");
    const mostViewed = advertisements.slice(0, 6);

    charts.advertisements = new window.Chart(
        document.querySelector("#advertisementViewsChart"),
        {
            type: "bar",
            data: {
                labels: mostViewed.map((advertisement) => advertisement.title),
                datasets: [{
                    label: "Views",
                    data: mostViewed.map((advertisement) => advertisement.view_count),
                    backgroundColor: "#65e5d8",
                    borderRadius: 7,
                    borderSkipped: false,
                }],
            },
            options: {
                indexAxis: "y",
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: { precision: 0 },
                        grid: { color: "rgba(255,255,255,0.06)" },
                    },
                    y: {
                        grid: { display: false },
                        ticks: { autoSkip: false },
                    },
                },
            },
        }
    );
}

function createCell(text) {
    const cell = document.createElement("td");
    cell.textContent = text;
    return cell;
}

function formatAudience(advertisement) {
    const gender = advertisement.target_gender === "all"
        ? "All visitors"
        : advertisement.target_gender;
    const minimum = advertisement.target_age_min;
    const maximum = advertisement.target_age_max;

    if (minimum === null && maximum === null) {
        return `${gender}, all ages`;
    }
    if (minimum !== null && maximum !== null) {
        return `${gender}, ${minimum}-${maximum}`;
    }
    return minimum !== null
        ? `${gender}, ${minimum}+`
        : `${gender}, up to ${maximum}`;
}

function actionButton(label, action, advertisementId, danger = false) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = danger
        ? "table-action table-action--danger"
        : "table-action";
    button.dataset.action = action;
    button.dataset.advertisementId = String(advertisementId);
    button.textContent = label;
    return button;
}

function renderAdvertisementTable(advertisements) {
    elements.advertisementTableBody.replaceChildren();
    elements.advertisementCount.textContent = `${advertisements.length} ${
        advertisements.length === 1 ? "advertisement" : "advertisements"
    }`;

    if (!advertisements.length) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");
        cell.colSpan = 6;
        cell.textContent = "No advertisements match these filters.";
        row.append(cell);
        elements.advertisementTableBody.append(row);
        return;
    }

    advertisements.forEach((advertisement) => {
        const row = document.createElement("tr");
        row.append(
            createCell(advertisement.title),
            createCell(formatAudience(advertisement)),
            createCell(advertisement.map_location || "Not assigned"),
            createCell(formatNumber(advertisement.view_count))
        );

        const statusCell = document.createElement("td");
        const status = document.createElement("span");
        status.className = advertisement.is_active
            ? "ad-status ad-status--active"
            : "ad-status ad-status--inactive";
        status.textContent = advertisement.is_active ? "Active" : "Inactive";
        statusCell.append(status);

        const actionCell = document.createElement("td");
        const actions = document.createElement("div");
        actions.className = "table-actions";
        actions.append(
            actionButton("Edit", "edit", advertisement.id),
            actionButton(
                advertisement.is_active ? "Pause" : "Activate",
                "toggle",
                advertisement.id
            ),
            actionButton("Delete", "delete", advertisement.id, true)
        );
        actionCell.append(actions);
        row.append(statusCell, actionCell);
        elements.advertisementTableBody.append(row);
    });
}

function showDashboardError(message) {
    elements.errorText.textContent = message;
    elements.error.hidden = false;
}

function hideDashboardError() {
    elements.error.hidden = true;
}

function showToast(message, isError = false) {
    clearTimeout(state.toastTimer);
    elements.toast.textContent = message;
    elements.toast.classList.toggle("is-error", isError);
    elements.toast.hidden = false;
    state.toastTimer = window.setTimeout(() => {
        elements.toast.hidden = true;
    }, 4200);
}

function populateStoreOptions() {
    const currentValue = elements.store.value;
    elements.store.replaceChildren();
    const emptyOption = document.createElement("option");
    emptyOption.value = "";
    emptyOption.textContent = "No store assigned";
    elements.store.append(emptyOption);

    state.stores.forEach((store) => {
        const option = document.createElement("option");
        option.value = String(store.id);
        option.textContent = `${store.name} — ${store.map_location}`;
        elements.store.append(option);
    });

    elements.store.value = currentValue;
}

async function loadAdvertisementInventory() {
    const parameters = new URLSearchParams();
    const search = elements.search.value.trim();
    const status = elements.statusFilter.value;

    if (search) {
        parameters.set("search", search);
    }
    if (status !== "all") {
        parameters.set("status", status);
    }

    const query = parameters.toString();
    const payload = await fetchJson(
        `/api/advertisements${query ? `?${query}` : ""}`
    );
    state.advertisements = payload.advertisements;
    renderAdvertisementTable(state.advertisements);
}

async function loadDashboard() {
    hideDashboardError();
    elements.refreshButton.disabled = true;
    elements.refreshButton.textContent = "Refreshing…";

    try {
        configureChartDefaults();
        const [statistics, demographics, advertisementStatistics, stores] =
            await Promise.all([
                fetchJson("/api/statistics"),
                fetchJson("/api/statistics/demographics"),
                fetchJson("/api/statistics/advertisements"),
                fetchJson("/api/stores"),
            ]);

        state.stores = stores.stores;
        populateStoreOptions();
        renderSummary(statistics);
        renderDailyChart(statistics.daily);
        renderGenderChart(demographics.gender);
        renderAgeChart(demographics.age_groups);
        renderAdvertisementChart(advertisementStatistics.advertisements);
        await loadAdvertisementInventory();
    } catch (error) {
        console.error(error);
        showDashboardError(error.message || "Dashboard data could not be loaded.");
    } finally {
        elements.refreshButton.disabled = false;
        elements.refreshButton.textContent = "Refresh data";
    }
}

function resetAdvertisementForm() {
    if (state.previewObjectUrl) {
        URL.revokeObjectURL(state.previewObjectUrl);
        state.previewObjectUrl = null;
    }

    elements.form.reset();
    elements.id.value = "";
    elements.isActive.checked = true;
    elements.gender.value = "all";
    elements.theme.value = "violet";
    elements.formError.hidden = true;
    elements.formError.textContent = "";
    elements.imagePreview.removeAttribute("src");
    elements.imagePreview.hidden = true;
    elements.imagePlaceholder.hidden = false;
}

function openCreateDialog() {
    resetAdvertisementForm();
    elements.dialogTitle.textContent = "Add advertisement";
    elements.saveButton.textContent = "Create advertisement";
    elements.dialog.showModal();
    elements.title.focus();
}

function openEditDialog(advertisement) {
    resetAdvertisementForm();
    elements.dialogTitle.textContent = "Edit advertisement";
    elements.saveButton.textContent = "Save changes";
    elements.id.value = String(advertisement.id);
    elements.title.value = advertisement.title || "";
    elements.description.value = advertisement.description || "";
    elements.category.value = advertisement.category || "";
    elements.gender.value = advertisement.target_gender || "all";
    elements.ageMin.value = advertisement.target_age_min ?? "";
    elements.ageMax.value = advertisement.target_age_max ?? "";
    elements.theme.value = advertisement.theme || "violet";
    elements.store.value = advertisement.store_id ?? "";
    elements.imagePath.value = advertisement.image_path || "";
    elements.qrUrl.value = advertisement.qr_code_url || "";
    elements.mapLocation.value = advertisement.map_location || "";
    elements.isActive.checked = Boolean(advertisement.is_active);

    if (advertisement.image_path) {
        elements.imagePreview.src = advertisement.image_path;
        elements.imagePreview.hidden = false;
        elements.imagePlaceholder.hidden = true;
    }

    elements.dialog.showModal();
    elements.title.focus();
}

function optionalNumber(input) {
    return input.value === "" ? null : Number(input.value);
}

function formPayload() {
    return {
        title: elements.title.value.trim(),
        description: elements.description.value.trim() || null,
        category: elements.category.value.trim(),
        target_gender: elements.gender.value,
        target_age_min: optionalNumber(elements.ageMin),
        target_age_max: optionalNumber(elements.ageMax),
        theme: elements.theme.value,
        store_id: elements.store.value || null,
        image_path: elements.imagePath.value.trim() || null,
        qr_code_url: elements.qrUrl.value.trim() || null,
        map_location: elements.mapLocation.value.trim() || null,
        is_active: elements.isActive.checked,
    };
}

async function uploadSelectedImage() {
    const image = elements.imageFile.files[0];

    if (!image) {
        return elements.imagePath.value.trim() || null;
    }

    const formData = new FormData();
    formData.append("image", image);

    const response = await fetch("/api/advertisements/upload", {
        method: "POST",
        headers: {
            Accept: "application/json",
            "X-CSRFToken": csrfToken(),
        },
        credentials: "same-origin",
        body: formData,
    });

    if (response.redirected || response.status === 401) {
        window.location.assign("/admin/login");
        throw new Error("Administrator session expired.");
    }

    let payload;

    try {
        payload = await response.json();
    } catch {
        throw new Error("The image upload returned an invalid response.");
    }

    if (!response.ok || !payload.success) {
        throw new Error(
            payload?.error?.message
            || "The advertisement image could not be uploaded."
        );
    }

    elements.imagePath.value = payload.image_url;
    return payload.image_url;
}

async function saveAdvertisement(event) {
    event.preventDefault();
    if (!elements.form.reportValidity()) {
        return;
    }

    const advertisementId = elements.id.value;
    const isEditing = Boolean(advertisementId);
    elements.formError.hidden = true;
    elements.saveButton.disabled = true;
    elements.saveButton.textContent = isEditing ? "Saving…" : "Creating…";

    try {
        const imagePath = await uploadSelectedImage();
        const advertisementPayload = formPayload();
        advertisementPayload.image_path = imagePath;

        const payload = await fetchJson(
            isEditing
                ? `/api/advertisements/${advertisementId}`
                : "/api/advertisements",
            {
                method: isEditing ? "PUT" : "POST",
                body: JSON.stringify(advertisementPayload),
            }
        );
        elements.dialog.close();
        showToast(payload.message);
        await loadDashboard();
    } catch (error) {
        elements.formError.textContent = error.message;
        elements.formError.hidden = false;
    } finally {
        elements.saveButton.disabled = false;
        elements.saveButton.textContent = isEditing
            ? "Save changes"
            : "Create advertisement";
    }
}

async function toggleAdvertisement(advertisement) {
    try {
        const payload = await fetchJson(
            `/api/advertisements/${advertisement.id}/status`,
            {
                method: "PATCH",
                body: JSON.stringify({ is_active: !advertisement.is_active }),
            }
        );
        showToast(payload.message);
        await loadDashboard();
    } catch (error) {
        showToast(error.message, true);
    }
}

function openDeleteDialog(advertisement) {
    state.pendingDeleteId = advertisement.id;
    elements.deleteName.textContent = advertisement.title;
    elements.deleteDialog.showModal();
}

async function confirmDeleteAdvertisement() {
    if (state.pendingDeleteId === null) {
        return;
    }

    elements.confirmDelete.disabled = true;
    elements.confirmDelete.textContent = "Deleting…";

    try {
        const payload = await fetchJson(
            `/api/advertisements/${state.pendingDeleteId}`,
            { method: "DELETE" }
        );
        elements.deleteDialog.close();
        state.pendingDeleteId = null;
        showToast(payload.message);
        await loadDashboard();
    } catch (error) {
        showToast(error.message, true);
    } finally {
        elements.confirmDelete.disabled = false;
        elements.confirmDelete.textContent = "Delete permanently";
    }
}

function handleTableAction(event) {
    const button = event.target.closest("[data-action]");
    if (!button) {
        return;
    }

    const advertisementId = Number(button.dataset.advertisementId);
    const advertisement = state.advertisements.find(
        (item) => item.id === advertisementId
    );

    if (!advertisement) {
        showToast("Advertisement data is no longer available.", true);
        return;
    }

    if (button.dataset.action === "edit") {
        openEditDialog(advertisement);
    } else if (button.dataset.action === "toggle") {
        toggleAdvertisement(advertisement);
    } else if (button.dataset.action === "delete") {
        openDeleteDialog(advertisement);
    }
}

elements.refreshButton.addEventListener("click", loadDashboard);
elements.addButton.addEventListener("click", openCreateDialog);
elements.closeDialog.addEventListener("click", () => elements.dialog.close());
elements.cancelButton.addEventListener("click", () => elements.dialog.close());
elements.form.addEventListener("submit", saveAdvertisement);
elements.advertisementTableBody.addEventListener("click", handleTableAction);
elements.statusFilter.addEventListener("change", () => {
    loadAdvertisementInventory().catch((error) => showToast(error.message, true));
});
elements.search.addEventListener("input", () => {
    clearTimeout(state.searchTimer);
    state.searchTimer = window.setTimeout(() => {
        loadAdvertisementInventory().catch((error) => showToast(error.message, true));
    }, 280);
});
elements.store.addEventListener("change", () => {
    const selectedStore = state.stores.find(
        (store) => String(store.id) === elements.store.value
    );
    if (selectedStore) {
        elements.mapLocation.value = selectedStore.map_location;
    }
});
elements.imageFile.addEventListener("change", () => {
    const image = elements.imageFile.files[0];

    if (!image) {
        return;
    }

    const allowedTypes = new Set([
        "image/jpeg",
        "image/png",
        "image/webp",
    ]);

    if (!allowedTypes.has(image.type)) {
        elements.imageFile.value = "";
        elements.formError.textContent = "Use a JPEG, PNG, or WebP image.";
        elements.formError.hidden = false;
        return;
    }

    if (image.size > 5 * 1024 * 1024) {
        elements.imageFile.value = "";
        elements.formError.textContent = "Advertisement images must be 5 MB or smaller.";
        elements.formError.hidden = false;
        return;
    }

    if (state.previewObjectUrl) {
        URL.revokeObjectURL(state.previewObjectUrl);
    }

    state.previewObjectUrl = URL.createObjectURL(image);
    elements.imagePreview.src = state.previewObjectUrl;
    elements.imagePreview.hidden = false;
    elements.imagePlaceholder.hidden = true;
    elements.formError.hidden = true;
});
elements.cancelDelete.addEventListener("click", () => {
    state.pendingDeleteId = null;
    elements.deleteDialog.close();
});
elements.confirmDelete.addEventListener("click", confirmDeleteAdvertisement);

loadDashboard();
