const BACKEND_URL = "http://localhost:5000";

function sendForReview() {
    const files = document.getElementById("fileInput").files;
    const email = document.getElementById("emailInput").value;
    if (files.length === 0 || !email) return alert("Please select file(s) and email");
  
    const formData = new FormData();
    for (let file of files) {
      formData.append("files", file);
    }
    formData.append("email", email);
  
    fetch(`${BACKEND_URL}/send-review`, {
      method: "POST",
      body: formData
    })
    .then(res => res.json())
    .then(() => {
      alert("File(s) sent!");
      loadFiles();
    });
  }
  

function uploadDraft() {
  const file = document.getElementById("draftFile").files[0];
  if (!file) return alert("Choose a draft file");

  const formData = new FormData();
  formData.append("file", file);

  fetch(`${BACKEND_URL}/upload-draft`, {
    method: "POST",
    body: formData
  })
  .then(res => res.json())
  .then(() => {
    alert("Draft uploaded!");
    loadFiles();
  });
}

function loadFiles() {
    fetch(`${BACKEND_URL}/files`)
      .then(res => res.json())
      .then(files => {
        const list = document.getElementById("fileList");
        list.innerHTML = '';
        files.forEach(f => {
          const row = document.createElement("tr");
          row.innerHTML = `
            <td>
              <strong>${f.filename}</strong><br>
              <a href="${BACKEND_URL}/download/original/${f.filename}" class="view-link" target="_blank">Original</a>
              ${f.hasDraft ? `<a href="${BACKEND_URL}/download/draft/${f.filename}" class="view-link" target="_blank">Draft</a>` : ''}
            </td>
            <td>
              ${f.hasDraft ? `<button class="file-action-btn" onclick="approve('${f.filename}')">Approve</button>` : ''}
              ${f.approved ? `<button class="file-action-btn" onclick="convertToPDF('${f.filename}')">Convert to PDF</button>` : ''}
              ${f.approved ? `<button class="file-action-btn" onclick="sendFinalPolicy('${f.filename}')">Send Final Policy</button>` : ''}
            </td>
          `;
          list.appendChild(row);
        });
      });
  }
  

function approve(filename) {
  fetch(`${BACKEND_URL}/approve`, {
    method: "POST",
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ filename })
  })
  .then(res => res.json())
  .then(() => {
    alert("Approved!");
    loadFiles();
  });
}

function convertToPDF(filename) {
    fetch(`${BACKEND_URL}/convert-pdf`, {
      method: "POST",
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename })
    })
    .then(res => res.json())
    .then(data => {
      if (data.pdf) {
        alert("PDF created successfully!");
        window.open(`${BACKEND_URL}/download/pdf/${data.pdf}`, "_blank");
      } else {
        alert("Failed to convert to PDF.");
      }
    });
  }
  
  function sendFinalPolicy(filename) {
    fetch(`${BACKEND_URL}/send-final-policy`, {
      method: "POST",
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename })
    })
    .then(res => res.json())
    .then(data => {
      if (data.message) {
        alert("Final policy sent via email!");
      } else {
        alert("Error sending final policy.");
      }
    });
  }
  

loadFiles();
