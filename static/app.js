function bakedApiUrl() {
  return String(window.MUSICALLY_API_URL || "").trim().replace(/\/$/, "");
}

function resolveApiBase() {
  const params = new URLSearchParams(window.location.search);
  const fromQuery = (params.get("api") || "").trim().replace(/\/$/, "");
  if (fromQuery) {
    localStorage.setItem("MUSICALLY_API_URL", fromQuery);
  }
  const stored = (localStorage.getItem("MUSICALLY_API_URL") || "").trim().replace(/\/$/, "");
  return stored || bakedApiUrl();
}

let API_BASE = resolveApiBase();

const urlInput = document.getElementById("url-input");
const fileInput = document.getElementById("file-input");
const apiUrlInput = document.getElementById("api-url-input");
const apiStatus = document.getElementById("api-status");
const extractBtn = document.getElementById("extract-btn");
const progressSection = document.getElementById("progress-section");
const progressStatus = document.getElementById("progress-status");
const progressPercent = document.getElementById("progress-percent");
const progressFill = document.getElementById("progress-fill");
const progressMessage = document.getElementById("progress-message");
const trackTitle = document.getElementById("track-title");
const resultsSection = document.getElementById("results-section");
const resultsTitle = document.getElementById("results-title");
const downloadBtn = document.getElementById("download-btn");
const errorSection = document.getElementById("error-section");
const errorMessage = document.getElementById("error-message");
const retryBtn = document.getElementById("retry-btn");

let currentJobId = null;
let pollTimer = null;

apiUrlInput.value = API_BASE;
updateApiStatus();

apiUrlInput.addEventListener("change", () => {
  API_BASE = apiUrlInput.value.trim().replace(/\/$/, "");
  if (API_BASE) {
    localStorage.setItem("MUSICALLY_API_URL", API_BASE);
  } else {
    localStorage.removeItem("MUSICALLY_API_URL");
  }
  updateApiStatus();
});

function updateApiStatus() {
  if (!API_BASE) {
    apiStatus.textContent =
      "Paste your Render URL here (the one that ends with .onrender.com). Vercel only hosts the UI.";
    return;
  }
  if (API_BASE.includes("vercel.app")) {
    apiStatus.textContent =
      "That looks like your Vercel site, not Render. Use the https://….onrender.com URL.";
    return;
  }
  apiStatus.textContent = `API: ${API_BASE}`;
}

function hideAllSections() {
  progressSection.classList.add("hidden");
  resultsSection.classList.add("hidden");
  errorSection.classList.add("hidden");
}

function showError(msg) {
  hideAllSections();
  errorMessage.textContent = msg;
  errorSection.classList.remove("hidden");
  extractBtn.disabled = false;
}

function updateProgress(job) {
  progressSection.classList.remove("hidden");
  progressStatus.textContent = job.status.replace("_", " ");
  progressPercent.textContent = `${job.progress}%`;
  progressFill.style.width = `${job.progress}%`;
  progressMessage.textContent = job.message;

  if (job.title) {
    trackTitle.textContent = `"${job.title}"`;
  }
}

function showResults(job) {
  hideAllSections();
  resultsSection.classList.remove("hidden");
  resultsTitle.textContent = job.title
    ? `"${job.title}" — drag this WAV into FL Studio.`
    : "WAV file ready for FL Studio.";
  downloadBtn.onclick = () => {
    window.location.href = `${API_BASE}/api/jobs/${job.id}/download`;
  };
  extractBtn.disabled = false;
}

async function readJson(res) {
  const text = await res.text();
  try {
    return JSON.parse(text);
  } catch {
    const snippet = text.replace(/\s+/g, " ").slice(0, 80);
    if (!API_BASE || API_BASE.includes("vercel.app")) {
      throw new Error(
        "The UI is calling the Vercel site instead of Render. Paste your Render URL (https://….onrender.com) in Backend URL, then try again."
      );
    }
    throw new Error(
      `Backend did not return JSON (${res.status}). ${snippet || "Empty response. Is the Render service live?"}`
    );
  }
}

async function pollJob(jobId) {
  try {
    const res = await fetch(`${API_BASE}/api/jobs/${jobId}`);
    const job = await readJson(res);
    if (!res.ok) throw new Error(job.detail || "Could not fetch job status.");

    updateProgress(job);

    if (job.status === "completed") {
      clearInterval(pollTimer);
      showResults(job);
    } else if (job.status === "failed") {
      clearInterval(pollTimer);
      showError(job.error || "Download failed.");
    }
  } catch (err) {
    clearInterval(pollTimer);
    showError(err.message);
  }
}

async function ensureBackend() {
  API_BASE = apiUrlInput.value.trim().replace(/\/$/, "");
  if (API_BASE) {
    localStorage.setItem("MUSICALLY_API_URL", API_BASE);
  }
  if (!API_BASE || API_BASE.includes("vercel.app")) {
    throw new Error(
      "Paste your Render backend URL in the Backend URL field (it should end with .onrender.com), not the Vercel site."
    );
  }
  const health = await fetch(`${API_BASE}/api/health`);
  const healthData = await readJson(health);
  if (!health.ok || !healthData.ok) {
    throw new Error(
      "Render backend is not ready yet. Open the Render URL in a browser, wait until it loads, then try again."
    );
  }
}

function watchJob(jobId) {
  currentJobId = jobId;
  pollTimer = setInterval(() => pollJob(currentJobId), 2000);
  pollJob(currentJobId);
}

async function startExtraction() {
  const url = urlInput.value.trim();
  if (!url) {
    urlInput.focus();
    return;
  }

  extractBtn.disabled = true;
  hideAllSections();
  progressSection.classList.remove("hidden");
  updateProgress({ status: "pending", progress: 0, message: "Connecting to backend..." });

  try {
    await ensureBackend();
    updateProgress({ status: "pending", progress: 5, message: "Submitting YouTube link..." });

    const res = await fetch(`${API_BASE}/api/process`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });

    const data = await readJson(res);
    if (!res.ok) throw new Error(data.detail || "Failed to start download.");
    watchJob(data.job_id);
  } catch (err) {
    showError(err.message);
  }
}

async function startFileExtraction(file) {
  if (!file) return;

  extractBtn.disabled = true;
  hideAllSections();
  progressSection.classList.remove("hidden");
  updateProgress({ status: "pending", progress: 0, message: `Uploading ${file.name}...` });

  try {
    await ensureBackend();
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API_BASE}/api/process-file`, {
      method: "POST",
      body: form,
    });
    const data = await readJson(res);
    if (!res.ok) throw new Error(data.detail || "Failed to start processing.");
    watchJob(data.job_id);
  } catch (err) {
    showError(err.message);
  }
}

extractBtn.addEventListener("click", startExtraction);
urlInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") startExtraction();
});

fileInput.addEventListener("change", () => {
  if (fileInput.files[0]) startFileExtraction(fileInput.files[0]);
});

retryBtn.addEventListener("click", () => {
  errorSection.classList.add("hidden");
  if (fileInput.files[0]) {
    startFileExtraction(fileInput.files[0]);
  } else {
    startExtraction();
  }
});

document.addEventListener("dragover", (e) => e.preventDefault());
document.addEventListener("drop", (e) => {
  e.preventDefault();
  const file = e.dataTransfer.files[0];
  if (file && file.type.startsWith("audio")) {
    startFileExtraction(file);
    return;
  }
  const text = e.dataTransfer.getData("text");
  if (text && (text.includes("youtube.com") || text.includes("youtu.be"))) {
    urlInput.value = text;
  }
});
