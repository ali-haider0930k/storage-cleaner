"use strict";

const state = {
  ready: false,
  drives: [],
  categories: [],
  scanResults: {},
  largeFilesRoots: [],
  largeFilesResult: null,
  selected: new Map(),
  batchScanId: null,
  lastCategoryScanId: {},
  lastLargeFilesScanId: null,
  busy: false,
};

const el = (id) => document.getElementById(id);
const api = () => window.pywebview?.api;

// ---------- Icons ----------
const ICONS = {
  temp: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>`,
  windows: `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M3 5.5L10.5 4.5v7.5H3zM3 12.5h7.5V20L3 19zM11.5 4.4L21 3v9h-9.5zM11.5 12.5H21V21l-9.5-1.4z"/></svg>`,
  trash: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>`,
  image: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>`,
  chrome: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3.5"/><line x1="12" y1="8.5" x2="20.5" y2="8.5"/><line x1="9" y1="14" x2="5" y2="20"/><line x1="15" y1="14" x2="19" y2="20"/></svg>`,
  edge: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 15.5-6.3M21 12a9 9 0 0 1-15 6.7"/><path d="M8 12h12a4 4 0 0 1-8 3"/></svg>`,
  firefox: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M4 8a6 6 0 0 1 10 0 5 5 0 0 1-3 9"/><path d="M12 4v4M8 10h4"/></svg>`,
  browser: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="16" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><circle cx="7" cy="6.5" r="0.5" fill="currentColor"/><circle cx="9.5" cy="6.5" r="0.5" fill="currentColor"/></svg>`,
  warning: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.3 3.86L1.82 18a2 2 0 0 0 1.7 3h16.96a2 2 0 0 0 1.7-3L13.7 3.86a2 2 0 0 0-3.4 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
  download: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>`,
  update: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15A9 9 0 1 1 19 5.35L23 10"/></svg>`,
  bolt: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>`,
  log: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="13" y2="17"/></svg>`,
  file: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><polyline points="13 2 13 9 20 9"/></svg>`,
};

// ---------- Formatting ----------
function humanBytes(n) {
  if (n === null || n === undefined) return "—";
  if (n === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.min(units.length - 1, Math.floor(Math.log(Math.abs(n)) / Math.log(1024)));
  const v = n / Math.pow(1024, i);
  return (i === 0 ? Math.round(v) : v.toFixed(v < 10 ? 2 : 1)) + " " + units[i];
}
function humanDate(ts) {
  if (!ts) return "—";
  const d = new Date(ts * 1000);
  const now = new Date();
  const diff = (now - d) / 86400000;
  if (diff < 1) return "today";
  if (diff < 2) return "yesterday";
  if (diff < 30) return Math.floor(diff) + "d ago";
  if (diff < 365) return Math.floor(diff / 30) + "mo ago";
  return Math.floor(diff / 365) + "y ago";
}
function basename(p) {
  if (!p) return "";
  const ix = Math.max(p.lastIndexOf("\\"), p.lastIndexOf("/"));
  return ix >= 0 ? p.slice(ix + 1) : p;
}

// ---------- Toast ----------
function toast(msg, kind = "info", ms = 3000) {
  const t = document.createElement("div");
  t.className = "toast " + kind;
  t.textContent = msg;
  el("toastWrap").appendChild(t);
  setTimeout(() => {
    t.style.opacity = "0";
    t.style.transition = "opacity 0.2s";
    setTimeout(() => t.remove(), 200);
  }, ms);
}

// ---------- Status ----------
function setStatus(text, mode = "idle") {
  el("statusText").textContent = text;
  const dot = el("statusDot");
  dot.classList.remove("busy", "error");
  if (mode === "busy") dot.classList.add("busy");
  if (mode === "error") dot.classList.add("error");
}
function showProgress(indeterminate = true, pct = 0) {
  const wrap = el("progressWrap");
  const bar = el("progressBar");
  wrap.classList.remove("hidden");
  if (indeterminate) {
    bar.classList.add("indeterminate");
    bar.style.width = "30%";
  } else {
    bar.classList.remove("indeterminate");
    bar.style.width = Math.min(100, Math.max(0, pct)) + "%";
  }
}
function hideProgress() {
  el("progressWrap").classList.add("hidden");
  el("progressBar").classList.remove("indeterminate");
  el("progressBar").style.width = "0%";
}

// ---------- Rendering ----------
function renderDrives() {
  const grid = el("drivesGrid");
  if (!state.drives.length) {
    grid.innerHTML = `<div class="drive-card" style="grid-column: 1/-1; text-align:center; color:var(--muted);">No fixed drives detected.</div>`;
    return;
  }
  grid.innerHTML = state.drives.map((d) => {
    const cls = d.percent >= 90 ? "high" : d.percent >= 70 ? "mid" : "low";
    return `
      <div class="drive-card">
        <div class="drive-head">
          <div class="drive-title">${escapeHtml(d.label || "Local Disk")}</div>
          <span class="drive-mount">${escapeHtml(d.mountpoint)}</span>
        </div>
        <div class="drive-usage" title="${d.percent.toFixed(1)}% used">
          <div class="drive-usage-fill ${cls}" style="width: ${d.percent}%"></div>
        </div>
        <div class="drive-meta">
          <span><strong>${humanBytes(d.free)}</strong> free</span>
          <span>${humanBytes(d.used)} of ${humanBytes(d.total)}</span>
        </div>
      </div>`;
  }).join("");
  el("drivesSummary").textContent = `${state.drives.length} drive${state.drives.length === 1 ? "" : "s"}`;
}

function renderCategories() {
  const grid = el("categoriesGrid");
  grid.innerHTML = state.categories.map((c) => {
    const res = state.scanResults[c.id];
    const hasRes = res && res.status === "done";
    const scanning = state.lastCategoryScanId[c.id] && res && res.status === "running";
    return `
      <div class="cat-card ${scanning ? "scanning" : ""} ${hasRes && res.total_files === 0 ? "done-empty" : ""}" data-cat="${c.id}">
        <div class="cat-head">
          <div class="cat-title">
            <span class="cat-icon">${ICONS[c.icon] || ICONS.file}</span>
            <span>${escapeHtml(c.label)}</span>
          </div>
          <span class="tier-badge tier-${c.tier}">${c.tier}</span>
        </div>
        <div class="cat-desc">${escapeHtml(c.desc)}</div>
        <div class="cat-stats">
          <div class="cat-stat">
            <span class="cat-stat-label">Files</span>
            <span class="cat-stat-value" data-role="files">${hasRes ? res.total_files.toLocaleString() : "—"}</span>
          </div>
          <div class="cat-stat">
            <span class="cat-stat-label">Size</span>
            <span class="cat-stat-value" data-role="bytes">${hasRes ? humanBytes(res.total_bytes) : "—"}</span>
          </div>
          ${scanning ? `<div class="cat-stat" style="margin-left:auto;"><span class="cat-scanning-indicator">scanning</span></div>` : ""}
        </div>
        <div class="cat-actions">
          <button class="btn btn-ghost" data-act="scan" data-cat="${c.id}">Scan</button>
          <button class="btn btn-primary" data-act="clean" data-cat="${c.id}" ${hasRes && res.total_files > 0 ? "" : "disabled"}>Clean</button>
        </div>
      </div>`;
  }).join("");
  updateOverview();
}

function updateOverview() {
  let cleanable = 0, cleanableFiles = 0;
  let safeB = 0, safeF = 0;
  let cautionB = 0, cautionF = 0;
  for (const c of state.categories) {
    const r = state.scanResults[c.id];
    if (!r || r.status !== "done") continue;
    cleanable += r.total_bytes;
    cleanableFiles += r.total_files;
    if (c.tier === "SAFE") { safeB += r.total_bytes; safeF += r.total_files; }
    if (c.tier === "CAUTION") { cautionB += r.total_bytes; cautionF += r.total_files; }
  }
  el("cleanableBytes").textContent = humanBytes(cleanable);
  el("cleanableFiles").textContent = cleanableFiles ? `${cleanableFiles.toLocaleString()} files` : "—";
  el("safeBytes").textContent = humanBytes(safeB);
  el("safeFiles").textContent = safeF ? `${safeF.toLocaleString()} files` : "—";
  el("cautionBytes").textContent = humanBytes(cautionB);
  el("cautionFiles").textContent = cautionF ? `${cautionF.toLocaleString()} files` : "—";
  el("btnCleanAllSafe").disabled = safeB === 0;
}

function renderLargeFilesRoots() {
  const wrap = el("lfRoots");
  wrap.innerHTML = state.largeFilesRoots.map((r, i) =>
    `<span class="lf-root-chip" title="${escapeHtml(r)}">
      ${escapeHtml(basename(r) || r)}
      <button data-remove-root="${i}" aria-label="Remove">×</button>
    </span>`
  ).join("");
}

function renderLargeFiles() {
  const tbody = el("lfBody");
  const r = state.largeFilesResult;
  if (!r || !r.items || r.items.length === 0) {
    tbody.innerHTML = r
      ? `<tr><td colspan="6" class="lf-empty">No files above the threshold. Try a smaller size.</td></tr>`
      : `<tr><td colspan="6" class="lf-empty">No scan yet. Click <b>Find</b> to begin.</td></tr>`;
    return;
  }
  tbody.innerHTML = r.items.map((f, i) => {
    const sel = state.selected.has(selKey("large_files", f.path));
    return `
      <tr data-path="${escapeAttr(f.path)}">
        <td class="col-check"><input type="checkbox" data-lfcheck="${i}" ${sel ? "checked" : ""}></td>
        <td class="file-name">${escapeHtml(basename(f.path))}</td>
        <td class="file-path" title="${escapeAttr(f.path)}">${escapeHtml(f.path)}</td>
        <td class="lf-size">${humanBytes(f.size)}</td>
        <td class="col-age">${humanDate(f.mtime)}</td>
        <td><button class="lf-open-btn" data-open="${escapeAttr(f.path)}">Open</button></td>
      </tr>`;
  }).join("");
}

function updateSelectionFooter() {
  const items = [...state.selected.values()];
  const totalBytes = items.reduce((s, it) => s + (it.size || 0), 0);
  const n = items.length;
  el("selectionText").textContent = n === 0
    ? "Nothing selected"
    : `${n.toLocaleString()} selected — ${humanBytes(totalBytes)}`;
  el("btnDeleteSelected").disabled = n === 0;
}

function selKey(catId, path) { return catId + "::" + path; }

function escapeHtml(s) {
  if (s == null) return "";
  return String(s).replace(/[&<>"']/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
}
function escapeAttr(s) { return escapeHtml(s); }

// ---------- Scan actions ----------
async function doScanAll() {
  if (state.busy) return;
  state.busy = true;
  el("btnScanAll").disabled = true;
  el("btnCancel").classList.remove("hidden");
  setStatus("Scanning all categories…", "busy");
  showProgress(true);
  state.scanResults = {};
  renderCategories();
  try {
    const { scan_id } = await api().scan_all_categories();
    state.batchScanId = scan_id;
  } catch (e) {
    setStatus("Scan failed to start: " + e, "error");
    toast("Scan failed: " + e, "error");
    state.busy = false;
    el("btnScanAll").disabled = false;
    el("btnCancel").classList.add("hidden");
    hideProgress();
  }
}

async function doScanCategory(catId) {
  const card = document.querySelector(`.cat-card[data-cat="${catId}"]`);
  if (card) card.classList.add("scanning");
  setStatus(`Scanning ${catId}…`, "busy");
  try {
    const { scan_id } = await api().scan_category(catId);
    state.lastCategoryScanId[catId] = scan_id;
  } catch (e) {
    setStatus("Scan failed: " + e, "error");
  }
}

async function doCleanCategory(catId) {
  const res = state.scanResults[catId];
  if (!res || res.total_files === 0) return;
  const cat = state.categories.find(c => c.id === catId);
  openDeleteModal({
    title: `Clean ${cat.label}?`,
    bodyHtml: `
      <p>This will ${cat.force_permanent ? "<b>permanently delete</b>" : "move to the Recycle Bin"}
      <b>${res.total_files.toLocaleString()} files</b> (${humanBytes(res.total_bytes)}).</p>
      <div class="modal-file-list">${res.items.slice(0, 10).map(i => escapeHtml(i.path)).join("<br>")}${res.items.length > 10 ? "<br>…" : ""}</div>
    `,
    permanent: !!cat.force_permanent,
    allowPermanentToggle: !cat.force_permanent && cat.tier !== "CAUTION",
    onConfirm: (permanent) => performDelete(catId, res.items.map(i => i.path), permanent),
  });
}

async function doCleanAllSafe() {
  const jobs = [];
  for (const c of state.categories) {
    if (c.tier !== "SAFE") continue;
    const r = state.scanResults[c.id];
    if (!r || r.total_files === 0) continue;
    jobs.push({ catId: c.id, paths: r.items.map(i => i.path), bytes: r.total_bytes, files: r.total_files, force: !!c.force_permanent });
  }
  if (jobs.length === 0) return;
  const totalFiles = jobs.reduce((s, j) => s + j.files, 0);
  const totalBytes = jobs.reduce((s, j) => s + j.bytes, 0);
  openDeleteModal({
    title: `Clean all SAFE categories?`,
    bodyHtml: `<p>This will clean <b>${jobs.length}</b> categories — <b>${totalFiles.toLocaleString()} files</b> (${humanBytes(totalBytes)}) — to the Recycle Bin.</p>`,
    permanent: false,
    allowPermanentToggle: true,
    onConfirm: async (permanent) => {
      for (const j of jobs) {
        await performDelete(j.catId, j.paths, permanent || j.force, /*silent*/ true);
      }
      toast(`Cleaned ${jobs.length} categories`, "success");
    },
  });
}

async function doFindLargeFiles() {
  if (state.busy) return;
  state.busy = true;
  el("btnFindLarge").disabled = true;
  el("btnBiggestOnPC").disabled = true;
  setStatus("Finding large files…", "busy");
  showProgress(true);
  try {
    const min = parseInt(el("lfMinSize").value, 10) || 100;
    const { scan_id } = await api().scan_large_files(state.largeFilesRoots, min, 500);
    state.lastLargeFilesScanId = scan_id;
  } catch (e) {
    setStatus("Scan failed: " + e, "error");
    state.busy = false;
    el("btnFindLarge").disabled = false;
    el("btnBiggestOnPC").disabled = false;
    hideProgress();
  }
}

async function doFindBiggestOnPC() {
  if (state.busy) return;
  state.busy = true;
  el("btnFindLarge").disabled = true;
  el("btnBiggestOnPC").disabled = true;
  el("btnCancel").classList.remove("hidden");
  setStatus("Scanning entire PC for 20 biggest files — may take several minutes…", "busy");
  showProgress(true);
  try {
    const { scan_id } = await api().scan_biggest_on_pc(20);
    state.lastLargeFilesScanId = scan_id;
  } catch (e) {
    setStatus("Scan failed: " + e, "error");
    state.busy = false;
    el("btnFindLarge").disabled = false;
    el("btnBiggestOnPC").disabled = false;
    el("btnCancel").classList.add("hidden");
    hideProgress();
  }
}

async function doAddRoot() {
  try {
    const picked = await api().choose_folder();
    if (picked && !state.largeFilesRoots.includes(picked)) {
      state.largeFilesRoots.push(picked);
      renderLargeFilesRoots();
    }
  } catch (e) { /* ignore */ }
}

function removeLargeFilesRoot(idx) {
  state.largeFilesRoots.splice(idx, 1);
  renderLargeFilesRoots();
}

async function performDelete(catId, paths, permanent, silent = false) {
  if (!paths || paths.length === 0) return;
  state.busy = true;
  el("btnDeleteSelected").disabled = true;
  setStatus(`Deleting ${paths.length.toLocaleString()} items…`, "busy");
  showProgress(false, 0);
  return new Promise((resolve) => {
    state._pendingDeleteResolve = () => {
      resolve();
      state._pendingDeleteResolve = null;
    };
    api().delete_files(catId, paths, !!permanent).then(resp => {
      if (resp && resp.error) {
        setStatus("Delete failed: " + resp.error, "error");
        toast("Delete failed: " + resp.error, "error");
        state.busy = false;
        hideProgress();
        state._pendingDeleteResolve = null;
        resolve();
      }
    }).catch(e => {
      setStatus("Delete failed: " + e, "error");
      toast("Delete failed: " + e, "error");
      state.busy = false;
      hideProgress();
      state._pendingDeleteResolve = null;
      resolve();
    });
  });
}

// ---------- Modal ----------
let _modalConfirm = null;
function openDeleteModal({ title, bodyHtml, permanent, allowPermanentToggle, onConfirm }) {
  el("modalTitle").textContent = title;
  el("modalBody").innerHTML = bodyHtml + (allowPermanentToggle ? `
    <label class="modal-option">
      <input type="checkbox" id="modalPermanent" ${permanent ? "checked" : ""}>
      <div class="modal-option-text">
        <span>Permanently delete (don't send to Recycle Bin)</span>
        <small>Freed space is immediate, but files can't be restored.</small>
      </div>
    </label>` : (permanent ? `<p style="color:var(--risky); margin-top:10px;"><b>Note:</b> this category bypasses the Recycle Bin.</p>` : ""));
  _modalConfirm = onConfirm;
  el("modalBackdrop").classList.remove("hidden");
}
function closeModal() {
  el("modalBackdrop").classList.add("hidden");
  _modalConfirm = null;
}
el("btnModalCancel").addEventListener("click", closeModal);
el("btnModalConfirm").addEventListener("click", () => {
  const permCb = el("modalPermanent");
  const perm = permCb ? permCb.checked : false;
  const fn = _modalConfirm;
  closeModal();
  if (fn) fn(perm);
});
el("modalBackdrop").addEventListener("click", (e) => {
  if (e.target.id === "modalBackdrop") closeModal();
});

// ---------- Event routing from Python ----------
window.__onEvent = (name, payload) => {
  if (name === "scan_progress") {
    setStatus(`Scanning ${payload.category_id}… ${payload.files_scanned?.toLocaleString() || 0} files`, "busy");
  } else if (name === "scan_complete") {
    state.scanResults[payload.category_id] = payload.result;
    renderCategories();
    if (payload.category_id === "large_files") {
      state.largeFilesResult = payload.result;
      renderLargeFiles();
      const n = payload.result.total_files;
      setStatus(n > 0 ? `Found ${n.toLocaleString()} large files (${humanBytes(payload.result.total_bytes)})` : "No large files found", "idle");
      state.busy = false;
      el("btnFindLarge").disabled = false;
      el("btnBiggestOnPC").disabled = false;
      el("btnCancel").classList.add("hidden");
      hideProgress();
    }
  } else if (name === "scan_all_progress") {
    setStatus(`Scanned ${payload.total_files?.toLocaleString() || 0} files — ${humanBytes(payload.total_bytes || 0)}`, "busy");
  } else if (name === "scan_all_complete") {
    setStatus(payload.status === "cancelled" ? "Scan cancelled" : `Scan complete — ${humanBytes(payload.total_bytes || 0)} can be reclaimed`, "idle");
    state.busy = false;
    state.batchScanId = null;
    el("btnScanAll").disabled = false;
    el("btnCancel").classList.add("hidden");
    hideProgress();
    if (payload.status === "done" && payload.total_bytes > 0) {
      toast(`Scan complete — ${humanBytes(payload.total_bytes)} can be freed`, "success", 4500);
    }
  } else if (name === "delete_progress") {
    const pct = payload.total > 0 ? (payload.done / payload.total) * 100 : 0;
    showProgress(false, pct);
    setStatus(`Deleting… ${payload.done.toLocaleString()} / ${payload.total.toLocaleString()}`, "busy");
  } else if (name === "delete_complete") {
    state.busy = false;
    hideProgress();
    const ok = payload.deleted || 0;
    const failed = (payload.failed || []).length;
    const freed = payload.bytes_freed || 0;
    setStatus(`Deleted ${ok.toLocaleString()} items — ${humanBytes(freed)} freed${failed ? ` (${failed} skipped)` : ""}`, failed ? "idle" : "idle");
    if (ok > 0) toast(`Freed ${humanBytes(freed)} (${ok.toLocaleString()} items)`, "success", 4500);
    if (failed > 0) toast(`${failed} items could not be deleted`, "error", 4000);
    // Refresh drives to reflect new free space
    refreshDrives();
    // Clear selection for deleted items
    state.selected.clear();
    updateSelectionFooter();
    // Re-render large files, removing deleted rows
    if (state.largeFilesResult) {
      state.largeFilesResult.items = state.largeFilesResult.items.filter(i => false);
      state.largeFilesResult.total_files = 0;
      state.largeFilesResult.total_bytes = 0;
      renderLargeFiles();
    }
    if (state._pendingDeleteResolve) state._pendingDeleteResolve();
  }
};

async function refreshDrives() {
  try {
    state.drives = await api().list_drives();
    renderDrives();
  } catch (e) { /* ignore */ }
}

// ---------- Event wiring ----------
el("btnScanAll").addEventListener("click", doScanAll);
el("btnCancel").addEventListener("click", async () => {
  const target = state.batchScanId || state.lastLargeFilesScanId;
  if (target) {
    try { await api().cancel_scan(target); } catch (e) {}
    setStatus("Cancelling…", "busy");
  }
});
el("btnCleanAllSafe").addEventListener("click", doCleanAllSafe);
el("btnAddRoot").addEventListener("click", doAddRoot);
el("btnFindLarge").addEventListener("click", doFindLargeFiles);
el("btnBiggestOnPC").addEventListener("click", doFindBiggestOnPC);

el("lfRoots").addEventListener("click", (e) => {
  const t = e.target.closest("[data-remove-root]");
  if (t) removeLargeFilesRoot(parseInt(t.dataset.removeRoot, 10));
});

el("categoriesGrid").addEventListener("click", (e) => {
  const t = e.target.closest("[data-act]");
  if (!t) return;
  const catId = t.dataset.cat;
  if (t.dataset.act === "scan") doScanCategory(catId);
  if (t.dataset.act === "clean") doCleanCategory(catId);
});

el("lfBody").addEventListener("click", (e) => {
  const openBtn = e.target.closest("[data-open]");
  if (openBtn) {
    api().open_folder(openBtn.dataset.open).catch(() => {});
    return;
  }
  const cb = e.target.closest("[data-lfcheck]");
  if (cb) {
    const idx = parseInt(cb.dataset.lfcheck, 10);
    const item = state.largeFilesResult.items[idx];
    if (!item) return;
    const k = selKey("large_files", item.path);
    if (cb.checked) state.selected.set(k, { category_id: "large_files", path: item.path, size: item.size });
    else state.selected.delete(k);
    updateSelectionFooter();
  }
});

el("lfSelectAll").addEventListener("change", (e) => {
  const checked = e.target.checked;
  if (!state.largeFilesResult) return;
  const items = state.largeFilesResult.items;
  for (const it of items) {
    const k = selKey("large_files", it.path);
    if (checked) state.selected.set(k, { category_id: "large_files", path: it.path, size: it.size });
    else state.selected.delete(k);
  }
  document.querySelectorAll("[data-lfcheck]").forEach(cb => cb.checked = checked);
  updateSelectionFooter();
});

el("btnDeleteSelected").addEventListener("click", () => {
  const entries = [...state.selected.values()];
  if (entries.length === 0) return;
  const byCategory = new Map();
  for (const it of entries) {
    if (!byCategory.has(it.category_id)) byCategory.set(it.category_id, []);
    byCategory.get(it.category_id).push(it.path);
  }
  const totalBytes = entries.reduce((s, it) => s + (it.size || 0), 0);
  openDeleteModal({
    title: "Delete selected?",
    bodyHtml: `<p>Delete <b>${entries.length.toLocaleString()}</b> selected items — ${humanBytes(totalBytes)}?</p>`,
    permanent: false,
    allowPermanentToggle: true,
    onConfirm: async (permanent) => {
      for (const [catId, paths] of byCategory) {
        await performDelete(catId, paths, permanent);
      }
    },
  });
});

// ---------- Bootstrap ----------
async function boot() {
  try {
    const [drives, categories, roots, version] = await Promise.all([
      api().list_drives(),
      api().list_categories(),
      api().default_large_roots(),
      api().get_version(),
    ]);
    state.drives = Array.isArray(drives) ? drives : [];
    state.categories = categories || [];
    state.largeFilesRoots = roots || [];
    el("appVersion").textContent = `v${version?.app || "1.0.0"}`;
    renderDrives();
    renderCategories();
    renderLargeFilesRoots();
    renderLargeFiles();
    updateSelectionFooter();
    setStatus("Ready. Click Scan All to begin.", "idle");
    state.ready = true;
  } catch (e) {
    setStatus("Startup error: " + e, "error");
    toast("Startup error: " + e, "error", 6000);
  }
}

if (window.pywebview && window.pywebview.api) {
  boot();
} else {
  window.addEventListener("pywebviewready", boot);
}
