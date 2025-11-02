/* ------ objectToText.js */
document.addEventListener("DOMContentLoaded", () => {
  const outputText = document.getElementById('outputText');
  // Clear the textbox on page load
  outputText.value = '';
});









/*

document.addEventListener("DOMContentLoaded", () => {
  const outputText = document.getElementById('outputText');
  outputText.value = '';

  // Helper to show a toast
  function showToast(message) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 2000);
  }

  // Attach click events to existing detected objects
  function makeObjectsClickable() {
    const objectSpans = document.querySelectorAll('#objectsGrid .object-name.clickable');
    objectSpans.forEach(span => {
      span.addEventListener('click', () => {
        const obj = span.textContent.toLowerCase(); // e.g., "PERSON" -> "person"

        fetch(`/type_object/${obj}`, { method: 'POST' })
          .then(res => res.json())
          .then(data => {
            if (data.typed_key) {
              outputText.value += data.typed_key;
              showToast(`Typed '${data.typed_key}' for ${obj}`);
            } else {
              showToast(`No mapping found for ${obj}`);
            }
          })
          .catch(err => {
            console.error("Error typing object:", err);
            showToast("Error sending request");
          });
      });
    });
  }

  // Initial attach
  makeObjectsClickable();

  // Optional: if objectsGrid updates dynamically, poll or use MutationObserver
  const observer = new MutationObserver(makeObjectsClickable);
  const grid = document.getElementById('objectsGrid');
  if (grid) {
    observer.observe(grid, { childList: true, subtree: true });
  }
});
*/



/*
// Show a toast notification
function showToast(message) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.classList.add("show");
  setTimeout(() => {
    toast.classList.remove("show");
  }, 2000);
}

document.addEventListener("DOMContentLoaded", () => {
  const typingGrid = document.getElementById('typingGrid');
  const outputText = document.getElementById('outputText');

  function updateDetectedObjects(detectedObjects) {
    typingGrid.innerHTML = ""; // Clear old buttons

    detectedObjects.forEach(obj => {
      const btn = document.createElement('button');
      btn.textContent = obj;
      btn.addEventListener('click', () => {
        fetch(`/type_object/${obj}`, { method: 'POST' })
          .then(response => response.json())
          .then(data => {
            if (data.typed_key) {
              outputText.value += data.typed_key;
              showToast(`Typed '${data.typed_key}' for ${obj}`);
            } else {
              showToast(`No mapping found for ${obj}`);
            }
          })
          .catch(err => {
            console.error("Error typing object:", err);
            showToast("Error sending request");
          });
      });
      typingGrid.appendChild(btn);
    });
  }

  // Example initial objects
  updateDetectedObjects(['apple', 'dog', 'banana', 'cup']);
});

*/

/*
async function pollDetectedObjects() {
  try {
    const res = await fetch("/get_detected_objects");
    const data = await res.json();
    updateDetectedObjects(data.objects_list || []);
  } catch (err) {
    console.error("Poll error:", err);
  }
}
setInterval(pollDetectedObjects, 1500);
*/



/*
document.addEventListener("DOMContentLoaded", () => {
    const objectsGrid = document.getElementById('objectsGrid');
    const outputText = document.getElementById('outputText');

    function updateDetectedObjects(detectedObjects) {
        objectsGrid.innerHTML = ""; // Clear old buttons
        detectedObjects.forEach(obj => {
            const btn = document.createElement('button');
            btn.textContent = obj;
            btn.addEventListener('click', () => {
                fetch(`/type_object/${obj}`, { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        outputText.value += data.typed_key;
                    })
                    .catch(err => console.error("Error typing object:", err));
            });
            objectsGrid.appendChild(btn);
        });
    }

    // Example: populate initially
    updateDetectedObjects(['apple', 'dog', 'banana', 'cup']);
}); */




/*
const objectsGrid = document.getElementById('objectsGrid');
const outputText = document.getElementById('outputText');

// Populate the objects grid with detected objects
function updateDetectedObjects(detectedObjects) {
    objectsGrid.innerHTML = ""; // Clear previous buttons
    detectedObjects.forEach(obj => {
        const btn = document.createElement('button');
        btn.textContent = obj;
        btn.addEventListener('click', () => {
            // Call Flask route to get typed key
            fetch(`/type_object/${obj}`, { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    outputText.value += data.typed_key; // Append typed key
                });
        });
        objectsGrid.appendChild(btn);
    });

}
*/

// Example usage: update the grid with new objects
// Call this every time YOLO detection gives you new objects
// updateDetectedObjects(['apple', 'dog', 'banana', 'cup']);

  
/*
// Call this function whenever you get new detected objects
function sendObjectsToServer(objects) {
    fetch("/type_objects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ objects: objects })
    })
    .then(response => response.json())
    .then(data => {
        const typedKeys = data.typed_keys;
        updateTypedTextBox(typedKeys);
    });
}

// Append typed keys to the textarea
function updateTypedTextBox(keys) {
    const textBox = document.getElementById("typedTextBox");
    keys.forEach(key => {
        textBox.value += key;
    });
}
*/