const root = document.getElementById("root");

const API_Endpoint = "/api/videosDownloaded";

async function load() {
  const res = await fetch(API_Endpoint);
  const json = await res.json();

  console.log(json);

  const set = new Set();

  json.forEach((channel) => {
    set.add(channel.channel);
  });

  for (const channel of set) {
    const card = document.createElement("div");
    card.className = "card video-card flex flex-col gap-6";

    card.innerHTML = `<h3>${channel}</h3>`;
    root.appendChild(card);
  }
}

load();
