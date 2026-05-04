const API = "/api/subscribePlaylist";

const listEl = document.getElementById("playlists");
const addBtn = document.getElementById("addBtn");
const refreshBtn = document.getElementById("refreshBtn");

addBtn.onclick = addPlaylist;
refreshBtn.onclick = loadPlaylists;

async function addPlaylist() {
  const status = document.getElementById("status");
  status.textContent = "Adding...";

  const extra = document
    .getElementById("extra_args")
    .value.split("\n")
    .map((x) => x.trim())
    .filter(Boolean);

  const prefrences = {
    output_dir: document.getElementById("output_dir").value || null,
    filename_template:
      document.getElementById("filename_template").value || null,
    audio_format: document.getElementById("audio_format").value || null,
    audio_only: document.getElementById("audio_only").checked,
    embed_metadata: document.getElementById("embed_metadata").checked,
    embed_thumbnail: document.getElementById("embed_thumbnail").checked,
    add_metadata: document.getElementById("add_metadata").checked,
    move_after: document.getElementById("move_after").checked,
    extra_args: extra.length ? extra : null,
  };
  const settings = {
    newPlaylistItem: "",
    PlaylistType: "",
  };

  const body = {
    url: document.getElementById("url").value,
    preferences: preferences,
    settings: settings,
  };

  console.log(body);

  try {
    const r = await fetch(API, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const data = await r.json();

    if (data.error) {
      status.textContent = data.error;
    } else {
      status.textContent = "Added";
      document.getElementById("url").value = "";
      loadPlaylists();
    }
  } catch {
    status.textContent = "Failed";
  }
}

async function loadPlaylists() {
  listEl.innerHTML = "Loading...";

  try {
    const r = await fetch(API);
    const playlists = await r.json();

    listEl.innerHTML = "";

    if (!playlists.length) {
      listEl.innerHTML = '<div class="text-muted">No playlists</div>';
      return;
    }

    playlists.forEach((playlist) => {
      listEl.appendChild(playlistCard(playlist));
    });
  } catch {
    listEl.innerHTML = '<div class="text-muted">Failed to load</div>';
  }
}

function playlistCard(playlist) {
  const div = document.createElement("div");
  div.className = "card p-3 flex flex-col gap-2";

  div.innerHTML = `
    <div class="flex justify-between items-center">
      <div class="text-sm font-mono">${playlist.id}</div>
      <button class="btn delete">Delete</button>
    </div>

    <div class="text-sm">
      <a href="${playlist.youtube_playlist_url}" target="_blank">
        ${playlist.youtube_playlist_url}
      </a>
    </div>

    <div class="text-xs text-muted">
      ${playlist.enabled ? "enabled" : "disabled"}
    </div>
  `;

  div.querySelector(".delete").onclick = () => deletePlaylist(playlist.id);

  return div;
}

async function deletePlaylist(id) {
  await fetch(API, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id }),
  });

  loadPlaylists();
}

loadPlaylists();
