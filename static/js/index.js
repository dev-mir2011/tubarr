function download() {
  localStorage.setItem(
    "yt-url",
    `${document.getElementById("download-url").value}`,
  );
  window.location.href = "/download";
}

async function thumbnails() {
  const res = await fetch("/api/generate_thumbnail_cache");
  await res.json(); // or await res.text()
  location.reload();
}
async function loadVideos() {
  const grid = document.getElementById("video-grid");
  grid.innerHTML = "Loading...";

  try {
    const res = await fetch("/api/videosDownloaded");
    const videos = await res.json();

    grid.innerHTML = "";

    if (!videos.length) {
      grid.innerHTML = `<div class="text-muted">No videos found</div>`;
      return;
    }

    videos.forEach((v) => {
      const card = document.createElement("div");
      card.className = "card video-card flex flex-col gap-2";

      const thumbUrl = `/api/thumbs/${encodeURIComponent(v.thumbnail)}`;

      card.innerHTML = `
  <img 
    src="${thumbUrl}" 
    class="video-thumb"
  />

  <div class="text-sm font-mono">
    ${v.name}
  </div>

  <div class="flex gap-2">
    <a class="link-muted text-sm" href="/api/videos/${encodeURIComponent(v.path)}">
      Open
    </a>

    <a class="link-muted text-sm" href="${thumbUrl}" target="_blank">
      Thumb
    </a>
  </div>
`;

      grid.appendChild(card);
    });
  } catch (err) {
    grid.innerHTML = `<div class="text-muted">Failed to load videos</div>`;
  }
}

loadVideos();
