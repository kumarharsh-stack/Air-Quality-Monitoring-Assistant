// Air Quality Assistant - frontend logic.
// No framework - plain fetch() calls to our own Flask API and Chart.js for the graph.

let currentLocation = null;
let historyChart = null;

const searchForm = document.getElementById("search-form");
const locationInput = document.getElementById("location-input");
const searchError = document.getElementById("search-error");

const resultCard = document.getElementById("result-card");
const historyCard = document.getElementById("history-card");
const predictCard = document.getElementById("predict-card");
const assistantCard = document.getElementById("assistant-card");

searchForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const location = locationInput.value.trim();
    if (!location) return;

    searchError.classList.add("hidden");

    try {
        const response = await fetch("/api/search", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ location }),
        });
        const data = await response.json();

        if (!response.ok) {
            showError(data.error || "Something went wrong.");
            return;
        }

        currentLocation = data.location;
        renderResult(data);
        revealCard(resultCard);
        revealCard(historyCard);
        revealCard(predictCard);
        revealCard(assistantCard);

        await loadHistory(currentLocation);
    } catch (err) {
        showError("Could not reach the server. Is app.py running?");
    }
});

function showError(message) {
    searchError.textContent = message;
    searchError.classList.remove("hidden");
}

function revealCard(el) {
    el.classList.remove("hidden");
}

function renderResult(data) {
    document.getElementById("result-location").textContent = data.location;

    const aqi = data.reading.us_aqi;
    document.getElementById("aqi-value").textContent = aqi ?? "N/A";
    document.getElementById("aqi-value").style.color = data.recommendation.color;

    document.getElementById("aqi-level").textContent = data.recommendation.level;
    document.getElementById("aqi-level").style.background = data.recommendation.color + "33"; // translucent bg
    document.getElementById("aqi-level").style.color = data.recommendation.color;

    document.getElementById("aqi-advice").textContent = data.recommendation.advice;

    document.getElementById("pm25-value").textContent = formatValue(data.reading.pm2_5);
    document.getElementById("pm10-value").textContent = formatValue(data.reading.pm10);
    document.getElementById("ozone-value").textContent = formatValue(data.reading.ozone);
    document.getElementById("no2-value").textContent = formatValue(data.reading.nitrogen_dioxide);
}

function formatValue(value) {
    return value === null || value === undefined ? "N/A" : value;
}

async function loadHistory(location) {
    const response = await fetch(`/api/history?location=${encodeURIComponent(location)}`);
    const data = await response.json();
    if (!response.ok) return;

    const labels = data.history.map((row) => new Date(row.recorded_at).toLocaleTimeString());
    const aqiValues = data.history.map((row) => row.us_aqi);

    const ctx = document.getElementById("history-chart").getContext("2d");

    if (historyChart) {
        historyChart.destroy();
    }

    historyChart = new Chart(ctx, {
        type: "line",
        data: {
            labels,
            datasets: [{
                label: "US AQI",
                data: aqiValues,
                borderColor: "#4ade80",
                backgroundColor: "rgba(74, 222, 128, 0.15)",
                tension: 0.3,
                fill: true,
            }],
        },
        options: {
            responsive: true,
            plugins: { legend: { labels: { color: "#e2e8f0" } } },
            scales: {
                x: { ticks: { color: "#94a3b8" } },
                y: { ticks: { color: "#94a3b8" } },
            },
        },
    });
}

// ---- ML Prediction ----
document.getElementById("predict-button").addEventListener("click", async () => {
    if (!currentLocation) return;
    const resultEl = document.getElementById("predict-result");
    resultEl.textContent = "Predicting...";

    const response = await fetch(`/api/predict?location=${encodeURIComponent(currentLocation)}`);
    const data = await response.json();

    if (!response.ok) {
        resultEl.textContent = data.error;
        return;
    }

    resultEl.textContent =
        `Predicted next PM2.5: ${data.predicted_pm2_5} µg/m³ ` +
        `(based on last readings: ${data.based_on_last_readings.join(", ")})`;
});

// ---- Assistant chat ----
const assistantForm = document.getElementById("assistant-form");
const assistantInput = document.getElementById("assistant-input");
const chatLog = document.getElementById("chat-log");

assistantForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const question = assistantInput.value.trim();
    if (!question) return;

    addChatMessage(question, "user");
    assistantInput.value = "";

    const response = await fetch("/api/assistant", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ location: currentLocation, question }),
    });
    const data = await response.json();
    addChatMessage(data.answer || data.error, "assistant");
});

function addChatMessage(text, role) {
    const div = document.createElement("div");
    div.className = `chat-message ${role}`;
    div.textContent = text;
    chatLog.appendChild(div);
    chatLog.scrollTop = chatLog.scrollHeight;
}
