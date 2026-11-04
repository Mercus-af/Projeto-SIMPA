const toggle = document.getElementById("menuToggle");
const seletorBase = document.getElementById("seletor-base");
if (seletorBase) seletorBase.addEventListener("change", () => window.location.assign(seletorBase.value));
const sidebar = document.getElementById("sidebar");
if (toggle && sidebar) toggle.addEventListener("click", () => sidebar.classList.toggle("sidebar-open"));

const tableSearch = document.getElementById("tableSearch");
if (tableSearch) {
  tableSearch.addEventListener("input", () => {
    const q = tableSearch.value.toLocaleLowerCase("pt-BR");
    document.querySelectorAll("#dataTable tbody tr").forEach(row => {
      row.hidden = !row.innerText.toLocaleLowerCase("pt-BR").includes(q);
    });
  });
}

const globalSearch = document.getElementById("globalSearch");
if (globalSearch) {
  globalSearch.addEventListener("keydown", e => {
    if (e.key === "Enter" && globalSearch.value.trim()) {
      window.location.href = `/alunos?q=${encodeURIComponent(globalSearch.value.trim())}`;
    }
  });
  document.addEventListener("keydown", e => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
      e.preventDefault(); globalSearch.focus();
    }
  });
}

const fileInput = document.getElementById("datasetFile");
const dropzone = document.getElementById("dropzone");
const fileName = document.getElementById("fileName");
const uploadMessage = document.getElementById("uploadMessage");
if (fileInput && dropzone) {
  const showFile = file => { if (file) fileName.textContent = `${file.name} · ${(file.size / 1024).toFixed(1)} KB`; };
  fileInput.addEventListener("change", () => showFile(fileInput.files[0]));
  ["dragenter", "dragover"].forEach(evt => dropzone.addEventListener(evt, e => { e.preventDefault(); dropzone.classList.add("dragging"); }));
  ["dragleave", "drop"].forEach(evt => dropzone.addEventListener(evt, e => { e.preventDefault(); dropzone.classList.remove("dragging"); }));
  dropzone.addEventListener("drop", e => { const f = e.dataTransfer.files[0]; if (f) { fileInput.files = e.dataTransfer.files; showFile(f); } });
  document.getElementById("uploadForm").addEventListener("submit", e => {
    e.preventDefault();
    const file = fileInput.files[0];
    if (!file) { uploadMessage.textContent = "Selecione um arquivo antes de continuar."; return; }
    const ext = file.name.split(".").pop().toLowerCase();
    if (!["csv", "json"].includes(ext)) { uploadMessage.textContent = "Formato inválido. Selecione CSV ou JSON."; return; }
    uploadMessage.textContent = "Arquivo selecionado e formato reconhecido. A importação real será conectada ao backend.";
  });
}
