const API_ENDPOINT = "/api/createPlaylistm3u";

const createButton = document.getElementById("createBtn");

createButton.addEventListener("click", async (e) => {
  document.getElementById("status").innerText = "Creating....";
  const res = await fetch(API_ENDPOINT, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      folder: `youtube/${document.getElementById("location").value}`,
      playlist_name: `${document.getElementById("playlist-name").value}.m3u`,
    }),
  });

  const json = await res.json();
  document.getElementById("status").innerText = "Created";
});
