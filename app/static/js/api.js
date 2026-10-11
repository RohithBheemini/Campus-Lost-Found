/**
 * OmniFind AI • API Client
 */

const API_BASE = "";

const api = {
  async getItems(params = {}) {
    const query = new URLSearchParams();
    if (params.item_type && params.item_type !== "all") query.append("item_type", params.item_type);
    if (params.category && params.category !== "all") query.append("category", params.category);
    if (params.location && params.location !== "all") query.append("location", params.location);
    if (params.status && params.status !== "all") query.append("status", params.status);
    if (params.search) query.append("search", params.search);
    if (params.limit) query.append("limit", params.limit);

    const res = await fetch(`${API_BASE}/api/items?${query.toString()}`);
    if (!res.ok) throw new Error("Failed to fetch items");
    return await res.json();
  },

  async getItemDetail(itemId) {
    const res = await fetch(`${API_BASE}/api/items/${itemId}`);
    if (!res.ok) throw new Error("Failed to fetch item details");
    return await res.json();
  },

  async createItem(formData) {
    const res = await fetch(`${API_BASE}/api/items`, {
      method: "POST",
      body: formData
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to create item");
    }
    return await res.json();
  },

  async getMatches(itemId, minConfidence = 0.15) {
    const res = await fetch(`${API_BASE}/api/match/${itemId}?min_confidence=${minConfidence}`);
    if (!res.ok) throw new Error("Failed to fetch item matches");
    return await res.json();
  },

  async submitClaim(claimData) {
    const res = await fetch(`${API_BASE}/api/claims`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(claimData)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to submit claim");
    }
    return await res.json();
  },

  async getStats() {
    const res = await fetch(`${API_BASE}/api/insights/stats`);
    if (!res.ok) throw new Error("Failed to fetch campus stats");
    return await res.json();
  },

  async getEvaluationMetrics() {
    const res = await fetch(`${API_BASE}/api/evaluation/metrics`);
    if (!res.ok) throw new Error("Failed to run evaluation benchmark");
    return await res.json();
  },

  async getNotifications(email = null) {
    const url = email ? `${API_BASE}/api/notifications?recipient_email=${encodeURIComponent(email)}` : `${API_BASE}/api/notifications`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to fetch notifications");
    return await res.json();
  },

  async markNotificationRead(id) {
    const res = await fetch(`${API_BASE}/api/notifications/${id}/read`, { method: "POST" });
    return await res.json();
  }
};

window.api = api;
