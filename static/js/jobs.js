const API = "/api/jobs";
const jobsEl = document.getElementById("jobs");
const refreshBtn = document.getElementById("refreshBtn");

refreshBtn.onclick = loadJobs;

async function loadJobs() {
  jobsEl.innerHTML = "Loading...";

  try {
    const r = await fetch(API);
    const jobs = await r.json();

    jobsEl.innerHTML = "";

    if (!jobs.length) {
      jobsEl.innerHTML = '<div class="text-muted">No jobs</div>';
      return;
    }

    jobs.forEach((job, index) => {
      jobsEl.appendChild(jobCard(job, index));
    });
  } catch (e) {
    jobsEl.innerHTML = '<div class="text-muted">Failed to load jobs</div>';
  }
}

function jobCard(job, index) {
  const div = document.createElement("div");
  div.className = "card p-3 flex flex-col gap-2";

  const statusColor =
    {
      queued: "#9aa4b2",
      downloading: "#4f8cff",
      finished: "#22c55e",
      error: "#ef4444",
    }[job.status] || "#9aa4b2";

  div.innerHTML = `
    <div class="flex justify-between items-center">
      <div class="text-sm font-mono">
        Job #${index + 1}
      </div>

      <div class="text-sm" style="color:${statusColor}">
        ${job.status}
      </div>
    </div>

    <div class="text-sm text-muted">
      ${job.url || ""}
    </div>

    ${
      job.error
        ? `
      <div class="text-xs font-mono" style="color:#ef4444; word-break: break-all;">
        ${job.error}
      </div>
    `
        : ""
    }
  `;

  return div;
}

loadJobs();
setInterval(loadJobs, 10000);
