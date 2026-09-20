const API_BASE = (window.MUSICALLY_API_URL || "").replace(/\/$/, "");

const STEM_ICONS = {
  drums: "🥁",
  bass: "🎸",
  other: "🎹",
  vocals: "🎤",
};

const urlInput = document.getElementById("url-input");
const extractBtn = document.getElementById("extract-btn");
const progressSection = document.getElementById("progress-section");
const progressStatus = document.getElementById("progress-status");
const progressPercent = document.getElementById("progress-percent");
const progressFill = document.getElementById("progress-fill");
const progressMessage = document.getElementById("progress-message");
const trackTitle = document.getElementById("track-title");
const resultsSection = document.getElementById("results-section");
const stemsGrid = document.getElementById("stems-grid");
const downloadAllBtn = document.getElementById("download-all-btn");
const errorSection = document.getElementById("error-section");
const errorMessage = document.getElementById("error-message");
const retryBtn = document.getElementById("retry-btn");

let currentJobId = null;
let pollTimer = null;

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
  stemsGrid.innerHTML = "";

  const stemOrder = ["drums", "bass", "other", "vocals"];
  for (const stem of stemOrder) {
    if (!job.stems[stem]) continue;

    const item = document.createElement("div");
    item.className = "stem-item";
    item.innerHTML = `
      <span class="stem-name">
        <span class="stem-icon">${STEM_ICONS[stem] || "🎵"}</span>
        ${stem}
      </span>
      <button class="stem-download" data-stem="${stem}">Download .wav</button>
    `;
    stemsGrid.appendChild(item);
  }

  stemsGrid.querySelectorAll(".stem-download").forEach((btn) => {
    btn.addEventListener("click", () => {
      window.location.href = `${API_BASE}/api/jobs/${job.id}/download/${btn.dataset.stem}`;
    });
  });

  downloadAllBtn.onclick = () => {
    window.location.href = `${API_BASE}/api/jobs/${job.id}/download-all`;
  };

  extractBtn.disabled = false;
}

async function pollJob(jobId) {
  try {
    const res = await fetch(`${API_BASE}/api/jobs/${jobId}`);
    if (!res.ok) throw new Error("Could not fetch job status.");
    const job = await res.json();

    updateProgress(job);

    if (job.status === "completed") {
      clearInterval(pollTimer);
      showResults(job);
    } else if (job.status === "failed") {
      clearInterval(pollTimer);
      showError(job.error || "Processing failed.");
    }
  } catch (err) {
    clearInterval(pollTimer);
    showError(err.message);
  }
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
  updateProgress({ status: "pending", progress: 0, message: "Submitting..." });

  try {
    const res = await fetch(`${API_BASE}/api/process`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to start processing.");

    currentJobId = data.job_id;
    pollTimer = setInterval(() => pollJob(currentJobId), 2000);
    pollJob(currentJobId);
  } catch (err) {
    showError(err.message);
  }
}

extractBtn.addEventListener("click", startExtraction);
urlInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") startExtraction();
});

retryBtn.addEventListener("click", () => {
  errorSection.classList.add("hidden");
  startExtraction();
});

// Allow drag-and-drop of URLs
document.addEventListener("dragover", (e) => e.preventDefault());
document.addEventListener("drop", (e) => {
  e.preventDefault();
  const text = e.dataTransfer.getData("text");
  if (text && (text.includes("youtube.com") || text.includes("youtu.be"))) {
    urlInput.value = text;
  }
});
