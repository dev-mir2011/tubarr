const API_ENDPOINT = "/api/createPlaylistm3u";

const createButton = document.getElementById("createBtn");

createButton.addEventListener("click", async (e) => {
  const res = await fetch(API_ENDPOINT, {
    method: "POST",
    body: {
      folder: document.getElementById("location").value,
      playlist_name: `${document.getElementById("playlist-name").value}.m3u`,
    },
  });
  document.getElementById("status").innerText = "Creating....";
  const json = await res.json();
  document.getElementById("status").innerText = "Created";
});
