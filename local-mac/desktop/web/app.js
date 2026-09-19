const API = "http://127.0.0.1:17891";
const $ = (id) => document.getElementById(id);

let pollTimer = null;

async function checkHealth() {
  try {
    const res = await fetch(API + "/api/health");
    if (!res.ok) throw new Error("offline");
    $("health").textContent = "Lokales Backend bereit";
    $("health").classList.add("ok");
  } catch {
    $("health").textContent = "Backend noch nicht bereit";
    setTimeout(checkHealth, 1200);
  }
}

function setProgress(job) {
  $("progressCard").classList.remove("hidden");
  $("progressMessage").textContent = job.message || job.status;
  $("progressPct").textContent = Math.round((job.progress || 0) * 100) + "%";
  $("barFill").style.width = Math.round((job.progress || 0) * 100) + "%";
  $("error").textContent = job.error || "";
}

function showClips(job) {
  $("results").innerHTML = "";
  $("resultCount").textContent = job.clips.length + " Clip(s)";
  for (const name of job.clips) {
    const card = document.createElement("article");
    card.className = "clip";
    const video = document.createElement("video");
    video.controls = true;
    video.preload = "metadata";
    video.src = API + "/api/jobs/" + job.id + "/clips/" + encodeURIComponent(name);
    const footer = document.createElement("footer");
    footer.textContent = name;
    card.append(video, footer);
    $("results").append(card);
  }
}

async function poll(id) {
  clearTimeout(pollTimer);
  const res = await fetch(API + "/api/jobs/" + id);
  const job = await res.json();
  setProgress(job);
  if (job.status === "done") {
    $("runBtn").disabled = false;
    showClips(job);
    return;
  }
  if (job.status === "failed") {
    $("runBtn").disabled = false;
    return;
  }
  pollTimer = setTimeout(() => poll(id), 800);
}

$("runBtn").addEventListener("click", async () => {
  const source = $("source").value.trim();
  if (!source) {
    $("source").focus();
    return;
  }
  $("runBtn").disabled = true;
  $("results").innerHTML = "";
  $("resultCount").textContent = "Analyse läuft …";
  $("progressCard").classList.remove("hidden");
  try {
    const res = await fetch(API + "/api/jobs", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        source,
        clips: Number($("clips").value),
        ollama_model: $("ollama").value.trim() || "qwen3:4b"
      })
    });
    if (!res.ok) throw new Error(await res.text());
    const job = await res.json();
    setProgress(job);
    poll(job.id);
  } catch (err) {
    $("runBtn").disabled = false;
    $("error").textContent = String(err);
  }
});

checkHealth();
