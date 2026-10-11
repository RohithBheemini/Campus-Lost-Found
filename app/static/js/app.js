/**
 * OmniFind AI • Main Application Controller
 */

let allLostItems = [];
let allFoundItems = [];
let currentFilterLocation = "all";
let currentQueryItemForMatch = null;
let currentClaimItem = null;
let selectedImageFile = null;

document.addEventListener("DOMContentLoaded", () => {
  setupNavigationTabs();
  loadAllData();
  init3DCampusScene();
  setupFormDateTimeDefault();
  setupDropZone();
  fetchNotifications();

  // Poll notifications every 30s
  setInterval(fetchNotifications, 30000);
});

// ==================== NAVIGATION TABS ====================
function setupNavigationTabs() {
  const tabs = document.querySelectorAll(".nav-btn");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");

      const targetId = tab.getAttribute("data-tab");
      document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
      const targetContent = document.getElementById(targetId);
      if (targetContent) targetContent.classList.add("active");

      if (targetId === "radar-tab") {
        setTimeout(() => {
          if (window.onWindowResize) window.onWindowResize();
        }, 100);
      } else if (targetId === "insights-tab") {
        loadCampusStats();
      }
    });
  });
}

function setupFormDateTimeDefault() {
  const input = document.getElementById("report-datetime");
  if (input) {
    const now = new Date();
    // format as YYYY-MM-DDTHH:MM
    const iso = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
    input.value = iso;
  }
}

// ==================== DATA LOADING ====================
async function loadAllData() {
  try {
    const [lost, found, stats] = await Promise.all([
      api.getItems({ item_type: "lost", limit: 100 }),
      api.getItems({ item_type: "found", limit: 100 }),
      api.getStats()
    ]);

    allLostItems = lost;
    allFoundItems = found;
    window.campusStatsData = stats;

    renderFeedItems();
    renderRadarLocations(stats.location_hotspots);
    updateStatsKPIs(stats);

    const totalRadarItems = document.getElementById("total-radar-items");
    if (totalRadarItems) totalRadarItems.textContent = `${lost.length + found.length} Items`;
  } catch (err) {
    console.error("Error loading data:", err);
    showToast("Error loading items from server", "error");
  }
}

// ==================== RENDER FEED ====================
function renderFeedItems() {
  const search = (document.getElementById("feed-search-input")?.value || "").toLowerCase().trim();
  const cat = document.getElementById("filter-category")?.value || "all";
  const loc = currentFilterLocation || "all";
  const typeFilter = document.getElementById("filter-type")?.value || "all";

  const filterFn = (item) => {
    if (cat !== "all" && item.category !== cat) return false;
    if (loc !== "all" && item.location !== loc) return false;
    if (search) {
      const matchTitle = (item.title || "").toLowerCase().includes(search);
      const matchDesc = (item.description || "").toLowerCase().includes(search);
      const matchBrand = (item.brand || "").toLowerCase().includes(search);
      const matchColor = (item.primary_color || "").toLowerCase().includes(search);
      if (!matchTitle && !matchDesc && !matchBrand && !matchColor) return false;
    }
    return true;
  };

  const filteredLost = typeFilter === "found" ? [] : allLostItems.filter(filterFn);
  const filteredFound = typeFilter === "lost" ? [] : allFoundItems.filter(filterFn);

  renderItemCards("lost-items-grid", filteredLost, "lost");
  renderItemCards("found-items-grid", filteredFound, "found");

  const lostCount = document.getElementById("lost-items-count");
  if (lostCount) lostCount.textContent = `${filteredLost.length} items`;

  const foundCount = document.getElementById("found-items-count");
  if (foundCount) foundCount.textContent = `${filteredFound.length} items`;
}

function renderItemCards(containerId, items, poolType) {
  const container = document.getElementById(containerId);
  if (!container) return;

  if (items.length === 0) {
    container.innerHTML = `<div class="empty-state" style="padding: 2rem; text-align: center; color: var(--text-dim);">No ${poolType} items matching criteria</div>`;
    return;
  }

  container.innerHTML = items.map(item => {
    const isLost = item.item_type === "lost";
    const imgHtml = item.image_url 
      ? `<img src="${item.image_url}" alt="${item.title}" class="item-thumb" onerror="this.src='/static/sample_images/keys_found.png'">`
      : `<span class="thumb-placeholder">${getCategoryIcon(item.category)}</span>`;

    const statusBadge = item.status !== "active" 
      ? `<span class="meta-chip" style="background: rgba(16, 185, 129, 0.2); color: var(--accent-emerald); font-weight: 700;">${item.status.toUpperCase()}</span>` 
      : "";

    const brandChip = item.brand 
      ? `<span class="meta-chip chip-brand">🏷️ ${item.brand}</span>` 
      : "";

    const colorChip = item.primary_color 
      ? `<span class="meta-chip chip-color"><span class="color-swatch-mini" style="background-color: ${getColorHex(item.primary_color)}"></span>${item.primary_color}</span>` 
      : "";

    return `
      <div class="item-card" data-id="${item.id}">
        <div class="item-thumb-wrap">
          ${imgHtml}
          <span class="item-type-badge ${isLost ? 'badge-lost' : 'badge-found'}">${item.item_type}</span>
        </div>
        
        <div class="item-info">
          <div>
            <div class="item-head-row">
              <h3 class="item-title">${escapeHtml(item.title)}</h3>
              ${statusBadge}
            </div>
            <p class="item-desc">${escapeHtml(item.description)}</p>
            
            <div class="item-meta-chips">
              <span class="meta-chip">📍 ${escapeHtml(item.location)}</span>
              ${brandChip}
              ${colorChip}
              <span class="meta-chip">🕒 ${formatDate(item.date_time)}</span>
            </div>
          </div>

          <div class="item-card-actions">
            <button class="card-btn card-btn-match" onclick="openMatchExplorer(${item.id})">
              🎯 AI Auto-Match
            </button>
            <button class="card-btn" onclick="openItemDetails(${item.id})">
              👁️ Details
            </button>
            ${!isLost && item.status === 'active' ? `
              <button class="card-btn card-btn-claim" onclick="openClaimModal(${item.id})">
                🛡️ Claim
              </button>
            ` : ''}
          </div>
        </div>
      </div>
    `;
  }).join("");
}

function getCategoryIcon(cat) {
  if (!cat) return "📦";
  if (cat.includes("Electronics")) return "💻";
  if (cat.includes("ID Cards")) return "🪪";
  if (cat.includes("Books")) return "📚";
  if (cat.includes("Bags")) return "🎒";
  if (cat.includes("Bottles")) return "🧴";
  if (cat.includes("Keys")) return "🔑";
  if (cat.includes("Accessories")) return "👓";
  if (cat.includes("Clothing")) return "🧥";
  return "📦";
}

function getColorHex(colorName) {
  const map = {
    "Black": "#18181b", "White": "#f4f4f5", "Space Gray": "#4b5563",
    "Silver": "#cbd5e1", "Navy Blue": "#1e3a8a", "Royal Blue": "#2563eb",
    "Sky Blue": "#38bdf8", "Crimson Red": "#dc2626", "Maroon / Burgundy": "#881337",
    "Forest Green": "#166534", "Lime Green": "#84cc16", "Gold / Yellow": "#eab308",
    "Orange": "#ea580c", "Purple": "#9333ea", "Pink": "#ec4899", "Brown": "#78350f"
  };
  return map[colorName] || "#94a3b8";
}

// ==================== RADAR SIDEBAR LOCATIONS ====================
function renderRadarLocations(hotspots) {
  const list = document.getElementById("radar-location-list");
  if (!list || !hotspots) return;

  list.innerHTML = hotspots.map(h => {
    const isSel = currentFilterLocation === h.location;
    return `
      <div class="loc-card ${isSel ? 'active' : ''}" onclick="selectLocationFilter('${escapeHtml(h.location)}')">
        <div class="loc-card-head">
          <span class="loc-name">📍 ${escapeHtml(h.location)}</span>
          <span class="loc-zone-tag">${h.total_activity} items</span>
        </div>
        <div class="loc-stats-mini">
          <span class="text-danger">Lost: ${h.lost_count}</span>
          <span class="text-success">Found: ${h.found_count}</span>
          <span class="text-cyan">Recovery: ${h.recovery_rate}%</span>
        </div>
      </div>
    `;
  }).join("");
}

function selectLocationFilter(locName) {
  currentFilterLocation = locName;
  const select = document.getElementById("filter-location");
  if (select) select.value = locName;

  renderFeedItems();
  if (window.campusStatsData) renderRadarLocations(window.campusStatsData.location_hotspots);

  // Focus building in 3D scene
  if (window.focusBuilding) window.focusBuilding(locName);

  showToast(`Filtered by ${locName}`, "info");
}
window.selectLocationFilter = selectLocationFilter;

function applyFeedFilters() {
  const selLoc = document.getElementById("filter-location")?.value;
  if (selLoc) currentFilterLocation = selLoc;
  renderFeedItems();
}

function resetFeedFilters() {
  document.getElementById("feed-search-input").value = "";
  document.getElementById("filter-type").value = "all";
  document.getElementById("filter-category").value = "all";
  document.getElementById("filter-location").value = "all";
  currentFilterLocation = "all";
  renderFeedItems();
  if (window.campusStatsData) renderRadarLocations(window.campusStatsData.location_hotspots);
  if (window.reset3DCamera) window.reset3DCamera();
}

function clearFeedSearch() {
  document.getElementById("feed-search-input").value = "";
  renderFeedItems();
}

// ==================== REAL-TIME AI ATTRIBUTE EXTRACTION ====================
let autoExtractTimeout = null;

function triggerAIAttributeAutoExtract() {
  clearTimeout(autoExtractTimeout);
  autoExtractTimeout = setTimeout(() => {
    const desc = document.getElementById("report-description")?.value || "";
    const title = document.getElementById("report-title")?.value || "";
    const previewBox = document.getElementById("ai-auto-preview");
    const tagsRow = document.getElementById("ai-preview-tags");
    if (!desc.trim()) {
      if (previewBox) previewBox.style.display = "none";
      return;
    }

    // Client-side quick preview regex matching
    const tags = [];
    const lower = `${title} ${desc}`.toLowerCase();

    // Brand detection
    const brands = ["apple", "macbook", "dell", "hp", "lenovo", "sony", "casio", "hydro flask", "nike", "fossil"];
    brands.forEach(b => {
      if (lower.includes(b)) {
        tags.push(`Brand: ${b.toUpperCase()}`);
        const brandInput = document.getElementById("report-brand");
        if (brandInput && !brandInput.value) brandInput.value = b.toUpperCase();
      }
    });

    // Color detection
    const colors = ["space gray", "silver", "black", "navy blue", "white", "red", "gold", "pink"];
    colors.forEach(c => {
      if (lower.includes(c)) {
        tags.push(`Color: ${c}`);
        const colorInput = document.getElementById("report-color");
        if (colorInput && !colorInput.value) colorInput.value = c;
      }
    });

    // Category
    if (lower.includes("laptop") || lower.includes("macbook") || lower.includes("phone") || lower.includes("headphones") || lower.includes("calculator")) {
      tags.push("Category: Electronics");
      document.getElementById("report-category").value = "Electronics & Gadgets";
    } else if (lower.includes("id card") || lower.includes("wallet") || lower.includes("lanyard")) {
      tags.push("Category: ID Cards");
      document.getElementById("report-category").value = "ID Cards & Wallets";
    } else if (lower.includes("bottle") || lower.includes("flask")) {
      tags.push("Category: Bottles");
      document.getElementById("report-category").value = "Bottles & Containers";
    }

    if (tags.length > 0) {
      if (previewBox) previewBox.style.display = "block";
      if (tagsRow) tagsRow.innerHTML = tags.map(t => `<span class="ai-tag">✨ ${t}</span>`).join("");
    } else {
      if (previewBox) previewBox.style.display = "none";
    }
  }, 300);
}

// ==================== IMAGE DRAG & DROP ====================
function setupDropZone() {
  const dropZone = document.getElementById("drop-zone");
  if (!dropZone) return;

  ["dragenter", "dragover"].forEach(evt => {
    dropZone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropZone.style.borderColor = "var(--accent-cyan)";
    });
  });

  ["dragleave", "drop"].forEach(evt => {
    dropZone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropZone.style.borderColor = "rgba(255, 255, 255, 0.15)";
    });
  });

  dropZone.addEventListener("drop", (e) => {
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleImageFile(e.dataTransfer.files[0]);
    }
  });
}

function handleImageSelection(event) {
  if (event.target.files && event.target.files.length > 0) {
    handleImageFile(event.target.files[0]);
  }
}

function handleImageFile(file) {
  if (!file.type.startsWith("image/")) {
    showToast("Please upload an image file (PNG, JPG)", "error");
    return;
  }
  selectedImageFile = file;

  const reader = new FileReader();
  reader.onload = (e) => {
    document.getElementById("image-preview").src = e.target.result;
    document.getElementById("drop-zone-content").style.display = "none";
    document.getElementById("image-preview-container").style.display = "flex";
  };
  reader.readAsDataURL(file);
}

function removeSelectedImage(event) {
  event.stopPropagation();
  selectedImageFile = null;
  document.getElementById("report-image-input").value = "";
  document.getElementById("image-preview").src = "";
  document.getElementById("drop-zone-content").style.display = "block";
  document.getElementById("image-preview-container").style.display = "none";
}

// ==================== REPORT ITEM FORM ====================
function openReportModal(type = "lost") {
  const modal = document.getElementById("report-modal");
  const title = document.getElementById("report-modal-title");
  const typeInput = document.getElementById("report-item-type");

  if (typeInput) typeInput.value = type;
  if (title) title.textContent = type === "lost" ? "Report Lost Item" : "Report Found Item";

  const challengeSub = document.querySelector(".challenge-sub");
  if (challengeSub) {
    challengeSub.textContent = type === "lost"
      ? "Set a secret verification question that proves you own this item (e.g. 'What sticker is on the laptop lid?')."
      : "Enter a question only the true owner would know to verify claims before custody handover.";
  }

  if (modal) modal.classList.add("show");
}

function closeReportModal() {
  const modal = document.getElementById("report-modal");
  if (modal) modal.classList.remove("show");
  document.getElementById("report-form").reset();
  removeSelectedImage({ stopPropagation: () => {} });
  setupFormDateTimeDefault();
}

async function submitReportForm(event) {
  event.preventDefault();
  const btn = document.getElementById("report-submit-btn");
  btn.disabled = true;
  btn.innerHTML = `<span>Processing AI Extractions...</span>`;

  try {
    const formData = new FormData();
    formData.append("title", document.getElementById("report-title").value);
    formData.append("description", document.getElementById("report-description").value);
    formData.append("category", document.getElementById("report-category").value);
    formData.append("location", document.getElementById("report-location").value);
    formData.append("specific_spot", document.getElementById("report-spot").value || "");
    formData.append("date_time", document.getElementById("report-datetime").value);
    formData.append("item_type", document.getElementById("report-item-type").value);
    formData.append("contact_name", document.getElementById("report-name").value);
    formData.append("contact_email", document.getElementById("report-email").value);
    formData.append("contact_phone", document.getElementById("report-phone").value || "");
    formData.append("brand", document.getElementById("report-brand").value || "");
    formData.append("primary_color", document.getElementById("report-color").value || "");
    formData.append("distinguishing_features", document.getElementById("report-features").value || "");
    formData.append("secret_verification_question", document.getElementById("report-secret-q").value || "");
    formData.append("secret_verification_answer", document.getElementById("report-secret-a").value || "");

    if (selectedImageFile) {
      formData.append("image", selectedImageFile);
    }

    const created = await api.createItem(formData);
    showToast(`Item reported! AI multi-modal features extracted.`, "success");
    closeReportModal();
    await loadAllData();

    // Trigger instant match explorer
    openMatchExplorer(created.id);
  } catch (err) {
    console.error("Report submit error:", err);
    showToast(err.message || "Failed to submit report", "error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span>Publish Report & Run AI Match</span>`;
  }
}

// ==================== MATCH EXPLORER ====================
async function openMatchExplorer(itemId) {
  const modal = document.getElementById("match-modal");
  const heroContainer = document.getElementById("match-query-hero");
  const listContainer = document.getElementById("match-candidates-list");
  const countBadge = document.getElementById("match-candidates-count");

  if (!modal) return;
  modal.classList.add("show");

  heroContainer.innerHTML = `<div class="loading-spinner">Loading query profile...</div>`;
  listContainer.innerHTML = `<div class="loading-spinner">Analyzing opposite pool with multi-modal embeddings...</div>`;

  try {
    const data = await api.getMatches(itemId, 0.10);
    currentQueryItemForMatch = data.query_item;

    const q = data.query_item;
    const isLost = q.item_type === "lost";

    // Query item banner
    heroContainer.innerHTML = `
      <div class="item-thumb-wrap">
        ${q.image_url ? `<img src="${q.image_url}" class="item-thumb">` : `<span class="thumb-placeholder">${getCategoryIcon(q.category)}</span>`}
        <span class="item-type-badge ${isLost ? 'badge-lost' : 'badge-found'}">${q.item_type}</span>
      </div>
      <div>
        <h3 style="font-size: 1.15rem; margin-bottom: 0.3rem;">${escapeHtml(q.title)}</h3>
        <p class="text-muted" style="font-size: 0.85rem; margin-bottom: 0.5rem;">${escapeHtml(q.description)}</p>
        <div class="item-meta-chips">
          <span class="meta-chip">🏷️ ${q.brand || 'Unspecified Brand'}</span>
          <span class="meta-chip">📍 ${q.location}</span>
          <span class="meta-chip">🎨 ${q.primary_color || 'Color auto-detect'}</span>
          <span class="meta-chip">🕒 ${formatDate(q.date_time)}</span>
        </div>
      </div>
    `;

    countBadge.textContent = `${data.candidates.length} Candidate Matches`;

    if (data.candidates.length === 0) {
      listContainer.innerHTML = `<div class="empty-state" style="padding: 2rem; text-align: center; color: var(--text-dim);">No candidate matches found in the opposite pool currently.</div>`;
      return;
    }

    listContainer.innerHTML = data.candidates.map(cand => {
      const c = cand.item;
      const b = cand.score_breakdown;
      const confPct = Math.round(b.overall_confidence * 100);
      const confClass = b.overall_confidence >= 0.75 ? 'conf-high' : (b.overall_confidence >= 0.50 ? 'conf-med' : 'conf-low');

      return `
        <div class="match-candidate-card">
          <div class="item-thumb-wrap">
            ${c.image_url ? `<img src="${c.image_url}" class="item-thumb">` : `<span class="thumb-placeholder">${getCategoryIcon(c.category)}</span>`}
          </div>

          <div>
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.3rem;">
              <h4 style="font-size: 1rem; font-weight: 700;">${escapeHtml(c.title)}</h4>
              <span class="badge-pill" style="border: 1px solid var(--border-glow);">${b.confidence_level} Confidence</span>
            </div>
            
            <p style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.4rem;">${escapeHtml(c.description)}</p>

            <div style="font-size: 0.78rem; color: var(--accent-cyan); margin-bottom: 0.4rem;">
              <strong>AI Rationale:</strong> ${escapeHtml(b.explanation)}
            </div>

            <div class="score-bars-breakdown">
              <div class="score-metric-row">
                <span>Text Semantics</span>
                <span>${Math.round(b.text_score * 100)}%</span>
              </div>
              <div class="score-metric-row">
                <span>Vision Match</span>
                <span>${Math.round(b.vision_score * 100)}%</span>
              </div>
              <div class="score-metric-row">
                <span>Attributes</span>
                <span>${Math.round(b.attribute_score * 100)}%</span>
              </div>
              <div class="score-metric-row">
                <span>Spatio-Temporal</span>
                <span>${Math.round(b.spatiotemporal_score * 100)}%</span>
              </div>
            </div>
          </div>

          <div class="confidence-box">
            <span class="confidence-ring ${confClass}">${confPct}%</span>
            <span style="font-size: 0.7rem; color: var(--text-dim);">Match Probability</span>
            
            ${c.item_type === 'found' && c.status === 'active' ? `
              <button class="card-btn card-btn-claim" style="width: 100%; margin-top: 0.5rem;" onclick="closeMatchModal(); openClaimModal(${c.id});">
                🛡️ Claim Item
              </button>
            ` : ''}
          </div>
        </div>
      `;
    }).join("");
  } catch (err) {
    console.error("Match error:", err);
    showToast("Failed to load match candidates", "error");
  }
}

function closeMatchModal() {
  const modal = document.getElementById("match-modal");
  if (modal) modal.classList.remove("show");
}

// ==================== CLAIM VERIFICATION ====================
async function openClaimModal(itemId) {
  const modal = document.getElementById("claim-modal");
  const summaryBox = document.getElementById("claim-item-summary");
  const qLabel = document.getElementById("claim-question-label");
  const itemInput = document.getElementById("claim-item-id");
  const resBox = document.getElementById("verification-result-box");

  if (!modal) return;
  modal.classList.add("show");
  if (resBox) resBox.style.display = "none";
  if (itemInput) itemInput.value = itemId;

  summaryBox.innerHTML = `<div class="loading-spinner">Loading item challenge...</div>`;

  try {
    const detail = await api.getItemDetail(itemId);
    currentClaimItem = detail.item;

    summaryBox.innerHTML = `
      <div style="display: flex; gap: 1rem; align-items: center;">
        <div class="item-thumb-wrap" style="width: 70px; height: 70px;">
          ${detail.item.image_url ? `<img src="${detail.item.image_url}" class="item-thumb">` : `<span class="thumb-placeholder">${getCategoryIcon(detail.item.category)}</span>`}
        </div>
        <div>
          <h4 style="font-size: 0.95rem;">${escapeHtml(detail.item.title)}</h4>
          <p class="text-muted" style="font-size: 0.75rem;">Found at ${escapeHtml(detail.item.location)} (${formatDate(detail.item.date_time)})</p>
        </div>
      </div>
    `;

    if (detail.item.secret_verification_question) {
      qLabel.textContent = `Challenge: "${detail.item.secret_verification_question}"`;
    } else {
      qLabel.textContent = `Ownership Challenge: Describe distinguishing marks, serial digits, or private stickers`;
    }
  } catch (err) {
    showToast("Failed to load challenge details", "error");
  }
}

function closeClaimModal() {
  const modal = document.getElementById("claim-modal");
  if (modal) modal.classList.remove("show");
  document.getElementById("claim-form").reset();
}

async function submitClaimForm(event) {
  event.preventDefault();
  const btn = document.getElementById("claim-submit-btn");
  const resBox = document.getElementById("verification-result-box");
  const statusRow = document.getElementById("result-status-row");
  const notesText = document.getElementById("result-notes-text");

  btn.disabled = true;
  btn.innerHTML = `<span>Evaluating AI Verification Challenge...</span>`;

  try {
    const claimData = {
      item_id: parseInt(document.getElementById("claim-item-id").value),
      claimant_name: document.getElementById("claimant-name").value,
      claimant_student_id: document.getElementById("claimant-student-id").value,
      claimant_email: document.getElementById("claimant-email").value,
      claimant_phone: document.getElementById("claimant-phone").value || null,
      secret_answer: document.getElementById("claim-secret-answer").value,
      additional_proof: document.getElementById("claim-additional-proof").value || null
    };

    const res = await api.submitClaim(claimData);
    resBox.style.display = "block";

    const scorePct = Math.round(res.verification_score * 100);

    if (res.verification_passed) {
      statusRow.innerHTML = `
        <span class="badge-pill" style="background: rgba(16, 185, 129, 0.2); color: var(--accent-emerald); font-weight: 800; font-size: 0.9rem;">
          ✅ OWNERSHIP VERIFIED (${scorePct}%)
        </span>
      `;
      notesText.innerHTML = `
        <strong>Verified!</strong> ${escapeHtml(res.verification_notes)}<br>
        <span style="color: var(--accent-cyan); display: inline-block; margin-top: 0.4rem;">
          📍 You can collect your item immediately at the Central Security Desk with your ID card (Student ID: ${res.claimant_student_id}).
        </span>
      `;
      showToast("Claim successfully verified!", "success");
      await loadAllData();
    } else {
      const isUnderReview = res.status === "under_review";
      statusRow.innerHTML = `
        <span class="badge-pill" style="background: ${isUnderReview ? 'rgba(245, 158, 11, 0.2)' : 'rgba(239, 68, 68, 0.2)'}; color: ${isUnderReview ? 'var(--accent-amber)' : 'var(--accent-danger)'}; font-weight: 800; font-size: 0.9rem;">
          ${isUnderReview ? '⚠️ UNDER MANUAL SECURITY REVIEW' : '❌ VERIFICATION FAILED'} (${scorePct}%)
        </span>
      `;
      notesText.textContent = res.verification_notes;
      showToast(isUnderReview ? "Claim submitted for manual staff review" : "Verification response did not match", "warning");
    }
  } catch (err) {
    showToast(err.message || "Failed to submit claim", "error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span>Verify Ownership & Submit Claim</span>`;
  }
}

// ==================== ITEM DETAILS & CUSTODY TIMELINE ====================
async function openItemDetails(itemId) {
  const modal = document.getElementById("detail-modal");
  const body = document.getElementById("detail-modal-body");
  if (!modal) return;
  modal.classList.add("show");

  body.innerHTML = `<div class="loading-spinner">Loading item details & 3D hologram...</div>`;

  try {
    const detail = await api.getItemDetail(itemId);
    const item = detail.item;
    const history = detail.custody_history || [];

    const distList = (item.distinguishing_features || []).map(f => `<span class="meta-chip">🔹 ${escapeHtml(f)}</span>`).join("");

    body.innerHTML = `
      <div style="display: grid; grid-template-columns: 320px 1fr; gap: 1.5rem;">
        <!-- Left: 3D Hologram Inspector & Visuals -->
        <div>
          <div style="background: rgba(0,0,0,0.4); border-radius: var(--radius-md); border: 1px solid var(--border-glow); overflow: hidden; height: 220px; position: relative;">
            <div id="hologram-viewport" style="width: 100%; height: 100%;"></div>
            <div style="position: absolute; bottom: 8px; left: 8px; font-size: 0.65rem; color: var(--accent-cyan); background: rgba(0,0,0,0.6); padding: 2px 6px; border-radius: 4px;">
              3D Hologram Inspector
            </div>
          </div>

          <div style="margin-top: 1rem; padding: 1rem; background: rgba(255,255,255,0.03); border-radius: var(--radius-md); border: 1px solid var(--border-subtle);">
            <h4 style="font-size: 0.85rem; margin-bottom: 0.5rem; color: var(--accent-cyan);">Visual CV Analysis</h4>
            <div style="display: flex; flex-direction: column; gap: 0.35rem; font-size: 0.78rem;">
              <div><strong>Primary Color:</strong> ${item.primary_color || 'Unknown'}</div>
              <div><strong>Brand:</strong> ${item.brand || 'Unspecified'}</div>
              <div><strong>Category:</strong> ${item.category}</div>
              <div><strong>Status:</strong> <span class="badge-pill">${item.status.toUpperCase()}</span></div>
            </div>
          </div>
        </div>

        <!-- Right: Description, Custody Timeline -->
        <div>
          <h2 style="font-size: 1.25rem; margin-bottom: 0.3rem;">${escapeHtml(item.title)}</h2>
          <p class="text-muted" style="font-size: 0.85rem; margin-bottom: 0.8rem;">${escapeHtml(item.description)}</p>

          <div style="margin-bottom: 1rem;">
            <strong style="font-size: 0.8rem; color: var(--text-muted); display: block; margin-bottom: 0.3rem;">Distinguishing Marks:</strong>
            <div style="display: flex; flex-wrap: wrap; gap: 0.4rem;">
              ${distList || '<span class="text-dim" style="font-size: 0.75rem;">None recorded</span>'}
            </div>
          </div>

          <div style="margin-bottom: 1rem;">
            <strong style="font-size: 0.85rem; color: var(--accent-cyan); display: block; margin-bottom: 0.6rem;">⛓️ Chain of Custody & Audit Timeline</strong>
            <div class="custody-timeline">
              ${history.map(h => `
                <div class="timeline-step">
                  <span class="timeline-dot"></span>
                  <div class="timeline-content">
                    <span class="timeline-action">${escapeHtml(h.action)}</span>
                    <span style="color: var(--text-dim); font-size: 0.7rem; margin-left: 0.4rem;">by ${escapeHtml(h.actor)} • ${formatDate(h.timestamp)}</span>
                    <p style="color: var(--text-muted); margin-top: 0.2rem;">${escapeHtml(h.details || '')}</p>
                  </div>
                </div>
              `).join("")}
            </div>
          </div>
        </div>
      </div>
    `;

    // Render 3D Hologram in left viewport
    setTimeout(() => {
      if (window.render3DItemHologram) {
        window.render3DItemHologram("hologram-viewport", item.category, item.brand, item.primary_color);
      }
    }, 50);

  } catch (err) {
    showToast("Failed to load item detail", "error");
  }
}

function closeDetailModal() {
  const modal = document.getElementById("detail-modal");
  if (modal) modal.classList.remove("show");
  if (window.cleanup3DHologram) {
    window.cleanup3DHologram();
  }
}

// ==================== CAMPUS STATS & INSIGHTS ====================
function updateStatsKPIs(stats) {
  const total = document.getElementById("stat-total-items");
  const lost = document.getElementById("stat-lost-items");
  const found = document.getElementById("stat-found-items");
  const rate = document.getElementById("stat-recovery-rate");
  const resolved = document.getElementById("stat-resolved-count");

  if (total) total.textContent = stats.total_lost + stats.total_found;
  if (lost) lost.textContent = stats.total_lost;
  if (found) found.textContent = stats.total_found;
  if (rate) rate.textContent = `${stats.overall_recovery_rate}%`;
  if (resolved) resolved.textContent = `${stats.total_resolved} cases resolved`;
}

async function loadCampusStats() {
  try {
    const stats = await api.getStats();
    window.campusStatsData = stats;
    updateStatsKPIs(stats);

    // Hotspots table
    const tbody = document.getElementById("hotspots-tbody");
    if (tbody && stats.location_hotspots) {
      const maxAct = Math.max(...stats.location_hotspots.map(h => h.total_activity), 1);
      tbody.innerHTML = stats.location_hotspots.map(h => {
        const pct = Math.round((h.total_activity / maxAct) * 100);
        return `
          <tr>
            <td><strong>📍 ${escapeHtml(h.location)}</strong></td>
            <td class="text-danger">${h.lost_count}</td>
            <td class="text-success">${h.found_count}</td>
            <td><strong>${h.total_activity}</strong></td>
            <td class="text-cyan">${h.recovery_rate}%</td>
            <td style="width: 140px;">
              <div class="cat-progress-track">
                <div class="cat-progress-fill" style="width: ${pct}%;"></div>
              </div>
            </td>
          </tr>
        `;
      }).join("");
    }

    // Category bars
    const catBars = document.getElementById("category-bars-list");
    if (catBars && stats.top_categories) {
      const maxCat = Math.max(...Object.values(stats.top_categories), 1);
      catBars.innerHTML = Object.entries(stats.top_categories).map(([cat, count]) => {
        const pct = Math.round((count / maxCat) * 100);
        return `
          <div class="cat-bar-item">
            <div class="cat-bar-label">
              <span>${getCategoryIcon(cat)} ${escapeHtml(cat)}</span>
              <strong>${count} items</strong>
            </div>
            <div class="cat-progress-track">
              <div class="cat-progress-fill" style="width: ${pct}%;"></div>
            </div>
          </div>
        `;
      }).join("");
    }
  } catch (err) {
    console.error("Stats load error:", err);
  }
}

// ==================== AI BENCHMARK LAB ====================
async function triggerEvaluationBenchmark() {
  const btn = document.getElementById("run-eval-btn");
  btn.disabled = true;
  btn.innerHTML = `<span class="eval-btn-icon">⏳</span> Running Inference Matrix...`;

  try {
    const res = await api.getEvaluationMetrics();

    document.getElementById("eval-top1").textContent = `${Math.round(res.top_1_accuracy * 100)}%`;
    document.getElementById("eval-top3").textContent = `${Math.round(res.top_3_accuracy * 100)}%`;
    document.getElementById("eval-mrr").textContent = res.mean_reciprocal_rank.toFixed(3);
    document.getElementById("eval-p1").textContent = res.precision_at_1.toFixed(3);
    document.getElementById("eval-p3").textContent = res.precision_at_3.toFixed(3);
    document.getElementById("eval-latency").textContent = `${res.avg_inference_latency_ms} ms`;

    document.getElementById("eval-dataset-meta").textContent = 
      `Evaluated ${res.num_ground_truth_pairs} Ground Truth Test Queries vs ${res.dataset_size} Candidates Pool (${res.distractors_count} Hard Distractors)`;

    const tbody = document.getElementById("eval-tbody");
    if (tbody && res.query_details) {
      tbody.innerHTML = res.query_details.map(q => {
        const isHit = q.rank === 1;
        return `
          <tr>
            <td><strong>${escapeHtml(q.query_title)}</strong></td>
            <td>${escapeHtml(q.true_match_title)}</td>
            <td>
              <span class="badge-pill" style="background: ${isHit ? 'rgba(16, 185, 129, 0.2)' : 'rgba(245, 158, 11, 0.2)'}; color: ${isHit ? 'var(--accent-emerald)' : 'var(--accent-amber)'}; font-weight: 800;">
                Rank #${q.rank}
              </span>
            </td>
            <td class="text-cyan"><strong>${Math.round(q.true_match_score * 100)}%</strong></td>
            <td style="font-size: 0.75rem; color: var(--text-muted);">${escapeHtml(q.explanation)}</td>
          </tr>
        `;
      }).join("");
    }

    showToast(`Benchmark completed! Top-1 Accuracy: ${Math.round(res.top_1_accuracy * 100)}% (${res.avg_inference_latency_ms}ms)`, "success");
  } catch (err) {
    showToast("Benchmark execution failed", "error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span class="eval-btn-icon">⚡</span> Run Live Benchmark`;
  }
}

// ==================== NOTIFICATIONS ====================
async function fetchNotifications() {
  try {
    const list = await api.getNotifications();
    const badge = document.getElementById("notif-badge");
    const container = document.getElementById("notif-list");

    const unreadCount = list.filter(n => !n.is_read).length;
    if (badge) {
      badge.textContent = unreadCount;
      badge.style.display = unreadCount > 0 ? "flex" : "none";
    }

    if (container) {
      if (list.length === 0) {
        container.innerHTML = `<div class="empty-state" style="padding: 1.5rem; text-align: center; color: var(--text-dim);">No alerts</div>`;
      } else {
        container.innerHTML = list.map(n => `
          <div class="notif-item">
            <div class="notif-item-title">${escapeHtml(n.title)}</div>
            <div>${escapeHtml(n.message)}</div>
            <div class="notif-item-time">${formatDate(n.created_at)}</div>
          </div>
        `).join("");
      }
    }
  } catch (err) {
    // Silent fail for polling
  }
}

function toggleNotifications() {
  const drop = document.getElementById("notif-dropdown");
  if (drop) drop.classList.toggle("show");
}

// ==================== UTILITIES ====================
function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  const icon = type === "success" ? "✅" : (type === "error" ? "❌" : (type === "warning" ? "⚠️" : "ℹ️"));
  toast.innerHTML = `<span>${icon}</span> <span>${escapeHtml(message)}</span>`;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function formatDate(isoStr) {
  if (!isoStr) return "";
  try {
    const d = new Date(isoStr);
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
  } catch {
    return isoStr;
  }
}

function escapeHtml(text) {
  if (!text) return "";
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

// Global exposure for inline events
window.openReportModal = openReportModal;
window.closeReportModal = closeReportModal;
window.submitReportForm = submitReportForm;
window.openMatchExplorer = openMatchExplorer;
window.closeMatchModal = closeMatchModal;
window.openClaimModal = openClaimModal;
window.closeClaimModal = closeClaimModal;
window.submitClaimForm = submitClaimForm;
window.openItemDetails = openItemDetails;
window.closeDetailModal = closeDetailModal;
window.triggerEvaluationBenchmark = triggerEvaluationBenchmark;
window.toggleNotifications = toggleNotifications;
window.fetchNotifications = fetchNotifications;
window.applyFeedFilters = applyFeedFilters;
window.resetFeedFilters = resetFeedFilters;
window.clearFeedSearch = clearFeedSearch;
window.handleImageSelection = handleImageSelection;
window.removeSelectedImage = removeSelectedImage;
window.triggerAIAttributeAutoExtract = triggerAIAttributeAutoExtract;
