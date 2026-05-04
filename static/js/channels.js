const API = "/api/subscribe";

const listEl = document.getElementById("channels");
const addBtn = document.getElementById("addBtn");
const refreshBtn = document.getElementById("refreshBtn");

addBtn.onclick = addChannel;
refreshBtn.onclick = loadChannels;

async function addChannel() {
  const status = document.getElementById("status");
  status.textContent = "Adding...";

  const extra = document
    .getElementById("extra_args")
    .value.split("\n")
    .map((x) => x.trim())
    .filter(Boolean);

  const preferences = {
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

  const body = {
    url: document.getElementById("url").value,
    prefrences: preferences,
  };

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
      loadChannels();
    }
  } catch {
    status.textContent = "Failed";
  }
}

async function loadChannels() {
  listEl.innerHTML = "Loading...";

  try {
    const r = await fetch(API);
    const channels = await r.json();

    listEl.innerHTML = "";

    if (!channels.length) {
      listEl.innerHTML = '<div class="text-muted">No channels</div>';
      return;
    }

    channels.forEach((ch) => {
      listEl.appendChild(channelCard(ch));
    });
  } catch {
    listEl.innerHTML = '<div class="text-muted">Failed to load</div>';
  }
}

function channelCard(ch) {
  const div = document.createElement("div");
  div.className = "card p-3 flex flex-col gap-2";

  div.innerHTML = `
    <div class="flex justify-between items-center">
      <div class="text-sm font-mono">${ch.id}</div>
      <button class="btn delete">Delete</button>
    </div>

    <div class="text-sm">
      <a href="${ch.youtube_url}" target="_blank">
        ${ch.youtube_url}
      </a>
    </div>

    <div class="text-xs text-muted">
      ${ch.enabled ? "enabled" : "disabled"}
    </div>
  `;

  div.querySelector(".delete").onclick = () => deleteChannel(ch.id);

  return div;
}

async function deleteChannel(id) {
  await fetch(API, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id }),
  });

  loadChannels();
}

loadChannels();
