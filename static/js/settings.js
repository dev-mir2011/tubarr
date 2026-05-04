const API = "/api/settings";

const channelScan = document.getElementById("channel_scan_interval");
const thumbScan = document.getElementById("generate_thumbnail_cache_interval");
const playlistScan = document.getElementById("playlist_scan_interval");
const status = document.getElementById("status");

document.getElementById("saveBtn").onclick = save;

async function load() {
  status.textContent = "Loading...";

  try {
    const r = await fetch(API);
    const data = await r.json();

    const settings = data.settings;

    channelScan.value = settings.channel_scan_interval;
    playlistScan.value = settings.scan_playlists_interval;
    thumbScan.value = settings.generate_thumbnail_cache_interval;

    status.textContent = "";
  } catch {
    status.textContent = "Failed to load";
  }
}

async function save() {
  status.textContent = "Saving...";

  const body = {
    channel_scan_interval: Number(channelScan.value),
    generate_thumbnail_cache_interval: Number(thumbScan.value),
    scan_playlists_interval: Number(playlistScan.value),
  };

  try {
    const r = await fetch(API, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    const data = await r.json();

    if (data.code === 201) {
      status.textContent = "Saved";
    } else {
      status.textContent = "Error";
    }
  } catch {
    status.textContent = "Failed";
  }
}

load();
