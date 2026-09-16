(function (root, factory) {
  const api = factory(root);
  if (typeof module === "object" && module.exports) module.exports = api;
  root.ClientOrdersFoundation = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function (root) {
  "use strict";
  const ORDER_STATES = ["rascunho", "aguardando_confirmacao", "aguardando_aprovacao", "aprovado", "cancelado", "convertido_em_venda", "erro", "duplicado_suspeito"];
  let currentOrders = [];

  function escapeHtml(value) {
    return String(value == null ? "" : value).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function filterOrders(orders, filters) {
    const source = Array.isArray(orders) ? orders : [];
    const active = filters || {};
    return source.filter(function (order) {
      if (active.client && !String(order.client_name || order.client || "").toLowerCase().includes(String(active.client).toLowerCase())) return false;
      if (active.company && order.company_key !== active.company && order.company !== active.company) return false;
      if (active.period && !String(order.created_at || "").startsWith(active.period)) return false;
      if (active.status && order.status !== active.status) return false;
      if (active.origin && String(order.origin || "whatsapp") !== active.origin) return false;
      if (active.withDamage && !order.withDamage && !order.with_damage) return false;
      if (active.aboveMaximum && !order.aboveMaximum && !order.above_maximum) return false;
      if (active.suspectedDuplicate && order.status !== "duplicado_suspeito") return false;
      if (active.awaitingApproval && order.status !== "aguardando_aprovacao") return false;
      return true;
    });
  }

  function render(orders) {
    const body = root.document && root.document.getElementById("client-orders-list");
    const summary = root.document && root.document.getElementById("client-orders-summary");
    if (!body) return;
    const items = Array.isArray(orders) ? orders : [];
    if (summary) summary.textContent = items.length + " pedido(s) em modo local";
    if (!items.length) { body.innerHTML = '<div class="client-orders-empty"><strong>Nenhum pedido recebido</strong><span>A estrutura esta pronta para simulacao local. Nenhuma venda sera criada automaticamente.</span></div>'; return; }
    body.innerHTML = '<div class="client-orders-table"><table><thead><tr><th>ID</th><th>Cliente</th><th>Data</th><th>Origem</th><th>Total</th><th>Status</th><th>Bloqueio</th></tr></thead><tbody>'
      + items.map(function (item) { const warning = item.status === "duplicado_suspeito" || item.status === "erro"; return '<tr><td>' + escapeHtml(String(item.id || "").slice(0, 8)) + '</td><td>' + escapeHtml(item.client_name || "Cliente") + '</td><td>' + escapeHtml(item.created_at || "") + '</td><td>WhatsApp</td><td>' + escapeHtml(item.total || "0") + '</td><td><span class="client-order-status ' + (warning ? "is-warning" : "") + '">' + escapeHtml(String(item.status || "").replace(/_/g, " ")) + '</span></td><td>' + escapeHtml(item.block_reason || "-") + '</td></tr>'; }).join("")
      + '</tbody></table></div>';
  }

  function readFilters() {
    const value = function (id) { const node = root.document && root.document.getElementById(id); return node ? node.value : ""; };
    const checked = function (id) { const node = root.document && root.document.getElementById(id); return !!(node && node.checked); };
    return { client: value("client-orders-client"), period: value("client-orders-period"), status: value("client-orders-status"), origin: value("client-orders-origin"), withDamage: checked("client-orders-damage"), aboveMaximum: checked("client-orders-maximum"), suspectedDuplicate: checked("client-orders-duplicate"), awaitingApproval: checked("client-orders-approval") };
  }

  function applyFilters() { render(filterOrders(currentOrders, readFilters())); }
  async function load() {
    try { currentOrders = await root.api("/api/whatsapp/orders"); applyFilters(); }
    catch (error) { currentOrders = []; render([]); const summary = root.document.getElementById("client-orders-summary"); if (summary) summary.textContent = error.message; }
  }

  return { ORDER_STATES, filterOrders, render, readFilters, applyFilters, load };
});
