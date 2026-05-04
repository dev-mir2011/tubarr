function load() {
  document.getElementById("url").value = localStorage.getItem("yt-url");
}

const urlType = document.getElementById("url-type");

urlType.addEventListener("change", function () {
  console.log("New value:", this.value);

  // example logic
  if (this.value === "playlist") {
    console.log("Playlist selected");
    document.getElementById("filename_template").value =
      "%(playlist_title)s/%(playlist_index)03d - %(title)s [%(id)s].%(ext)s";
  } else if (this.value === "video") {
    console.log("Video selected");
    document.getElementById("filename_template").value =
      "%(title)s [%(id)s].%(ext)s";
  }
});

const API = "/api/download";
document.getElementById("downloadBtn").onclick = async () => {
  const status = document.getElementById("status");
  status.textContent = "Starting...";
  const extra = document
    .getElementById("extra_args")
    .value.split("\n")
    .map((x) => x.trim())
    .filter(Boolean);
  const body = {
    url: document.getElementById("url").value,
    output_dir: document.getElementById("output_dir").value || undefined,
    filename_template:
      document.getElementById("filename_template").value || undefined,
    audio_format: document.getElementById("audio_format").value || undefined,
    audio_only: document.getElementById("audio_only").checked,
    embed_metadata: document.getElementById("embed_metadata").checked,
    embed_thumbnail: document.getElementById("embed_thumbnail").checked,
    add_metadata: document.getElementById("add_metadata").checked,
    move_after: document.getElementById("move_after").checked,
    extra_args: extra.length ? extra : undefined,
  };
  try {
    const r = await fetch(API, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await r.json();
    console.log(data);
    if (data.job_id) {
      status.textContent = "Started: " + data.job_id;
    } else {
      status.textContent = "Error: " + (data.error || "unknown");
    }
  } catch (e) {
    status.textContent = "Request failed";
  }
};

load();
