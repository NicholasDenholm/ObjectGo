/* ------ homepage.js */
const responseEl = document.getElementById("response");
const videoEl = document.getElementById("videoStream");
const placeholderEl = document.getElementById("videoPlaceholder");
const objectsPanel = document.getElementById("objectsPanel");
const objectsGrid = document.getElementById("objectsGrid");
const outputText = document.getElementById("outputText");

// we'll store poll timer here so we can stop it
let pollTimer = null;

// Helper to show a toast
function showToast(message) {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 2000);
}

function renderObjects(objs) {
  objectsPanel.style.display = "block";
  objectsGrid.innerHTML = "";

  const entries = Object.entries(objs || {});
  if (entries.length === 0) {
    objectsGrid.innerHTML = `<div style="text-align:center; color:#94a3b8; font-size:0.8rem;">No objects detected yet...</div>`;
    return;
  }

  // Sort by detection count (descending)
  entries.sort((a, b) => b[1] - a[1]);

  entries.forEach(([name, count]) => {
    const row = document.createElement("div");
    row.className = "object-row";

    // Make name clickable
    const label = document.createElement("span");
    label.className = "object-name clickable";
    label.textContent = name.toUpperCase();

    label.addEventListener("click", () => {
      const objName = name.toLowerCase();
      console.log(`Clicking object: ${objName}`);
      
      fetch(`/type_object/${objName}`, { method: "POST" })
        .then(res => res.json())
        .then(data => {
          console.log('Response data:', data);
          
          if (data.typed_key) {
            // Check for special commands
            if (data.typed_key === "__BACKSPACE__") {
              // Remove last character
              outputText.value = outputText.value.slice(0, -1);
              showToast(`Backspace for ${objName}`);
            } else {
              // Normal text append
              outputText.value += data.typed_key;
              showToast(`Typed '${data.typed_key}' for ${objName}`);
            }
          } else {
            showToast(`No mapping found for ${objName}`);
            console.warn(`No typed_key returned for ${objName}`);
          }
        })
        .catch(err => {
          console.error("Error typing object:", err);
          showToast("Error sending request");
        });
    });

    const countEl = document.createElement("span");
    countEl.className = "object-count";
    countEl.textContent = count;

    row.append(label, countEl);
    objectsGrid.appendChild(row);
  });
}

// START MODEL
document.getElementById("startModelBtn").addEventListener("click", async () => {
  const res = await fetch("/api/start_model");
  const data = await res.json();
  responseEl.textContent = data.message;

  // show video
  videoEl.src = "/video_feed";
  videoEl.style.display = "block";
  placeholderEl.style.display = "none";

  // start polling every 1.5s for latest detections
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(async () => {
    try {
      const r = await fetch("/api/request");
      const d = await r.json();
      renderObjects(d.objects || {});
    } catch (err) {
      console.log("poll error", err);
    }
  }, 1500);
});

// STOP MODEL
document.getElementById("stopModelBtn").addEventListener("click", async () => {
  const res = await fetch("/api/stop_model");
  const data = await res.json();
  responseEl.textContent = data.message;

  videoEl.style.display = "none";
  videoEl.removeAttribute("src");
  placeholderEl.style.display = "block";

  // stop polling
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }

  // clear object counter
  objectsGrid.innerHTML = "";
  objectsPanel.style.display = "none";
});


/*
const responseEl = document.getElementById("response");
const videoEl = document.getElementById("videoStream");
const placeholderEl = document.getElementById("videoPlaceholder");
const objectsPanel = document.getElementById("objectsPanel");
const objectsGrid = document.getElementById("objectsGrid");

// we'll store poll timer here so we can stop it
let pollTimer = null;


function renderObjects(objs) {
  const objectsGrid = document.getElementById("objectsGrid");
  const outputText = document.getElementById("outputText");
  const objectsPanel = document.getElementById("objectsPanel");

  objectsPanel.style.display = "block";
  objectsGrid.innerHTML = "";

  const entries = Object.entries(objs || {});
  if (entries.length === 0) {
    objectsGrid.innerHTML = `<div style="text-align:center; color:#94a3b8; font-size:0.8rem;">No objects detected yet...</div>`;
    return;
  }

  // Sort by detection count (descending)
  entries.sort((a, b) => b[1] - a[1]);

  entries.forEach(([name, count]) => {
    const row = document.createElement("div");
    row.className = "object-row";

    // 🟢 Make name clickable
    const label = document.createElement("span");
    label.className = "object-name clickable";
    label.textContent = name.toUpperCase();

    label.addEventListener("click", () => {
      fetch(`/type_object/${name}`, { method: "POST" })
        .then(res => res.json())
        .then(data => {
          outputText.value += data.typed_key || "";
        })
        .catch(err => console.error("Error typing object:", err));
    });

    const countEl = document.createElement("span");
    countEl.className = "object-count";
    countEl.textContent = count;

    row.append(label, countEl);
    objectsGrid.appendChild(row);
  });
}
*/

/* OLD Working non text render function */
/*
// render function
function renderObjects(objs) {
  objectsPanel.style.display = "block";
  objectsGrid.innerHTML = "";

  const entries = Object.entries(objs || {});
  if (entries.length === 0) {
    objectsGrid.innerHTML = `<div style="text-align:center; color:#94a3b8; font-size:0.8rem;">No objects detected yet...</div>`;
    return;
  }

  // sort by count/value desc
  entries.sort((a, b) => b[1] - a[1]);

  entries.forEach(([name, count]) => {
    const row = document.createElement("div");
    row.className = "object-row";

    const label = document.createElement("span");
    label.className = "object-name";
    label.textContent = name.toUpperCase();

    const countEl = document.createElement("span");
    countEl.className = "object-count";
    countEl.textContent = count;

    row.append(label, countEl);
    objectsGrid.appendChild(row);
  });
}
*/

/*
// START MODEL
document.getElementById("startModelBtn").addEventListener("click", async () => {
  const res = await fetch("/api/start_model");
  const data = await res.json();
  responseEl.textContent = data.message;

  // show video
  videoEl.src = "/video_feed";
  videoEl.style.display = "block";
  placeholderEl.style.display = "none";

  // start polling every 1.5s for latest detections
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(async () => {
    try {
      const r = await fetch("/api/request");
      const d = await r.json();
      renderObjects(d.objects || {});
    } catch (err) {
      console.log("poll error", err);
    }
  }, 1500);
});

// STOP MODEL
document.getElementById("stopModelBtn").addEventListener("click", async () => {
  const res = await fetch("/api/stop_model");
  const data = await res.json();
  responseEl.textContent = data.message;

  videoEl.style.display = "none";
  videoEl.removeAttribute("src");
  placeholderEl.style.display = "block";

  // stop polling
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }

  // ✅ clear object counter
  objectsGrid.innerHTML = "";
  objectsPanel.style.display = "none";
});
*/

/*
// Call this function whenever you get new detected objects
function updateDetectedObjects(detectedObjects) {
    // Clear the old buttons (optional)
    objectsGrid.innerHTML = '';

    detectedObjects.forEach(obj => {
        const btn = document.createElement('button');
        btn.textContent = obj;
        btn.addEventListener('click', () => {
            fetch(`/type_object/${obj}`, { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    outputText.value += data.typed_key;
                });
        });
        objectsGrid.appendChild(btn);
    });
}
*/