(function (root, factory) {
  const api = factory(root);
  if (typeof module === "object" && module.exports) module.exports = api;
  root.ClientOrdersFoundation = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function (root) {
  "use strict";
  const ORDER_STATES = ["rascunho", "aguardando_confirmacao", "aguardando_aprovacao", "aprovado", "cancelado", "convertido_em_venda", "erro", "duplicado_suspeito"];
  const PENDING_STATES = ["rascunho", "aguardando_confirmacao", "aguardando_aprovacao"];
  const PRODUCT_LABELS = { MAC_PCT: "Macaxeira com casca", MAC_VACUO: "Macaxeira a vacuo", ALHO_250G: "Alho descascado 250g", ALHO_KG: "Alho descascado 1kg", MAC_CHIPS: "Macaxeira chips", PRE_COZIDA: "Macaxeira pre-cozida" };
  let currentOrders = [];
  let eventsBound = false;

  function escapeHtml(value) {
    return String(value == null ? "" : value).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function isRaiosModule() {
    return !(root.document && root.document.body && root.document.body.classList && root.document.body.classList.contains("company-estrada"));
  }

  function formatMoney(value) {
    const number = Number(value || 0);
    return Number.isFinite(number) ? number.toLocaleString("pt-BR", { style: "currency", currency: "BRL" }) : "R$ 0,00";
  }

  function formatDate(value) {
    const text = String(value || "").trim();
    if (!text) return "Nao informado";
    const parsed = new Date(text.indexOf("T") >= 0 ? text : text.replace(" ", "T") + "Z");
    return Number.isNaN(parsed.getTime()) ? text : parsed.toLocaleString("pt-BR");
  }

  function statusLabel(value) { return String(value || "nao informado").replace(/_/g, " "); }

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

  function pendingOrders(orders) {
    return (Array.isArray(orders) ? orders : []).filter(function (order) { return PENDING_STATES.indexOf(order.status) >= 0; });
  }

  function clientOrders(orders, clientId) {
    return (Array.isArray(orders) ? orders : []).filter(function (order) { return String(order.client_id || "") === String(clientId || ""); });
  }

  function renderNotifications(orders) {
    if (!root.document || !isRaiosModule()) return;
    const badge = root.document.getElementById("mdr-orders-bell-badge");
    const list = root.document.getElementById("mdr-orders-notification-list");
    const items = pendingOrders(orders);
    if (badge) {
      badge.textContent = items.length > 99 ? "99+" : String(items.length);
      badge.classList.toggle("is-empty", items.length === 0);
    }
    if (!list) return;
    list.innerHTML = items.length ? items.slice(0, 8).map(function (item) {
      return '<button type="button" class="client-orders-notification-item" data-client-order-id="' + escapeHtml(item.id) + '"><strong>' + escapeHtml(item.client_name || "Cliente") + '</strong><span>'
        + escapeHtml(statusLabel(item.status)) + ' · ' + escapeHtml(formatMoney(item.total)) + ' · ' + escapeHtml(formatDate(item.created_at)) + '</span></button>';
    }).join("") : '<div class="client-orders-notification-empty">Nenhum pedido novo ou pendente.</div>';
  }

  function render(orders) {
    const body = root.document && root.document.getElementById("client-orders-list");
    const summary = root.document && root.document.getElementById("client-orders-summary");
    if (!body) return;
    const items = Array.isArray(orders) ? orders : [];
    if (summary) summary.textContent = items.length + " pedido(s)";
    renderNotifications(currentOrders);
    if (!items.length) {
      body.innerHTML = '<div class="client-orders-empty"><strong>Nenhum pedido recebido</strong><span>Este cliente ainda não possui pedidos ou nenhum pedido corresponde aos filtros.</span></div>';
      return;
    }
    body.innerHTML = '<div class="client-orders-table"><table><thead><tr><th>ID</th><th>Cliente</th><th>Data</th><th>Origem</th><th>Total</th><th>Status</th><th>Bloqueio</th></tr></thead><tbody>' + items.map(function (item) {
      const warning = item.status === "duplicado_suspeito" || item.status === "erro";
      return '<tr class="client-order-row" tabindex="0" data-client-order-id="' + escapeHtml(item.id) + '" aria-label="Abrir pedido de ' + escapeHtml(item.client_name || "Cliente") + '"><td>'
        + escapeHtml(String(item.id || "").slice(0, 8)) + '</td><td><button type="button" class="client-order-client" data-client-order-id="' + escapeHtml(item.id) + '">' + escapeHtml(item.client_name || "Cliente")
        + '</button></td><td>' + escapeHtml(formatDate(item.created_at)) + '</td><td>WhatsApp</td><td>' + escapeHtml(formatMoney(item.total)) + '</td><td><span class="client-order-status '
        + (warning ? "is-warning" : "") + '">' + escapeHtml(statusLabel(item.status)) + '</span></td><td>' + escapeHtml(item.block_reason || "-") + '</td></tr>';
    }).join("") + '</tbody></table></div>';
  }

  function readFilters() {
    const value = function (id) { const node = root.document && root.document.getElementById(id); return node ? node.value : ""; };
    const checked = function (id) { const node = root.document && root.document.getElementById(id); return !!(node && node.checked); };
    return { client: value("client-orders-client"), period: value("client-orders-period"), status: value("client-orders-status"), origin: value("client-orders-origin"), withDamage: checked("client-orders-damage"), aboveMaximum: checked("client-orders-maximum"), suspectedDuplicate: checked("client-orders-duplicate"), awaitingApproval: checked("client-orders-approval") };
  }

  function applyFilters() { render(filterOrders(currentOrders, readFilters())); }

  function orderListHtml(orders, activeId) {
    if (!orders.length) return '<div class="client-orders-client-empty">Este cliente ainda não possui pedidos</div>';
    return '<div class="client-orders-client-list">' + orders.map(function (order) {
      return '<button type="button" data-client-order-id="' + escapeHtml(order.id) + '" class="' + (String(order.id) === String(activeId) ? "is-selected" : "") + '"><strong>Pedido '
        + escapeHtml(String(order.id || "").slice(0, 8)) + '</strong><small>' + escapeHtml(formatDate(order.created_at)) + ' · ' + escapeHtml(statusLabel(order.status))
        + '</small><strong>' + escapeHtml(formatMoney(order.total)) + '</strong></button>';
    }).join("") + '</div>';
  }

  function orderItemsHtml(items) {
    if (!items || !items.length) return '<div class="client-orders-client-empty">Nenhum item registrado neste pedido.</div>';
    return items.map(function (item) {
      const quantity = item.confirmed_quantity || item.requested_quantity || "0";
      return '<div class="client-orders-item"><strong>' + escapeHtml(PRODUCT_LABELS[item.product_key] || item.product_key || "Produto") + '</strong><span>Quantidade: ' + escapeHtml(quantity)
        + ' · Total: ' + escapeHtml(formatMoney(item.total)) + '</span><span>Avaria: ' + escapeHtml(item.confirmed_damage || "0") + '</span></div>';
    }).join("");
  }

  function orderHistoryHtml(history) {
    if (!history || !history.length) return '<div class="client-orders-client-empty">Nenhum histórico de processamento registrado.</div>';
    return history.map(function (entry) {
      return '<div class="client-orders-history"><strong>' + escapeHtml(statusLabel(entry.new_status)) + '</strong><span>' + escapeHtml(formatDate(entry.created_at))
        + (entry.reason ? ' · ' + escapeHtml(entry.reason) : '') + (entry.changed_by ? ' · ' + escapeHtml(entry.changed_by) : '') + '</span></div>';
    }).join("");
  }

  function buildClientDetailHtml(client, orders, detail) {
    const safeClient = client || {};
    let html = '<div class="client-orders-client-card"><strong>' + escapeHtml(safeClient.client_name || "Cliente") + '</strong><span>WhatsApp: ' + escapeHtml(safeClient.client_phone || "Nao informado")
      + '</span></div>' + orderListHtml(orders || [], detail && detail.id);
    if (!orders || !orders.length) return html;
    if (!detail) return html + '<div class="client-orders-detail-loading">Carregando pedido...</div>';
    html += '<section class="client-orders-detail-section"><h4>Resumo do pedido</h4><div class="client-orders-detail-grid">'
      + '<div class="client-orders-detail-field"><small>Data</small><strong>' + escapeHtml(formatDate(detail.created_at)) + '</strong></div>'
      + '<div class="client-orders-detail-field"><small>Status</small><strong>' + escapeHtml(statusLabel(detail.status)) + '</strong></div>'
      + '<div class="client-orders-detail-field"><small>Total</small><strong>' + escapeHtml(formatMoney(detail.total)) + '</strong></div>'
      + '<div class="client-orders-detail-field"><small>Origem</small><strong>WhatsApp</strong></div></div></section>'
      + '<section class="client-orders-detail-section"><h4>Itens e informações solicitadas</h4>' + orderItemsHtml(detail.items) + '</section>'
      + '<section class="client-orders-detail-section"><h4>Histórico e processamento</h4>' + orderHistoryHtml(detail.history) + '</section>';
    return html;
  }

  function showDetailShell(order) {
    const panel = root.document && root.document.getElementById("client-orders-detail");
    const overlay = root.document && root.document.getElementById("client-orders-detail-overlay");
    const title = root.document && root.document.getElementById("client-orders-detail-title");
    const body = root.document && root.document.getElementById("client-orders-detail-body");
    if (!panel || !overlay || !body) return null;
    panel.hidden = false;
    overlay.hidden = false;
    if (title) title.textContent = order.client_name || "Detalhes do pedido";
    body.innerHTML = buildClientDetailHtml(order, clientOrders(currentOrders, order.client_id), null);
    return body;
  }

  async function openOrder(orderId) {
    const order = currentOrders.find(function (item) { return String(item.id) === String(orderId); });
    if (!order || !root.document) return null;
    const notificationList = root.document.getElementById("mdr-orders-notification-list");
    const bell = root.document.getElementById("mdr-orders-bell");
    if (notificationList) notificationList.hidden = true;
    if (bell) bell.setAttribute("aria-expanded", "false");
    const body = showDetailShell(order);
    if (!body) return null;
    try {
      const detail = await root.api("/api/whatsapp/orders/" + encodeURIComponent(order.id));
      body.innerHTML = buildClientDetailHtml(detail, clientOrders(currentOrders, order.client_id), detail);
      return detail;
    } catch (error) {
      body.innerHTML = '<div class="client-orders-detail-error"><strong>Não foi possível abrir este pedido.</strong><br>' + escapeHtml(error.message || "Pedido inexistente") + '</div>';
      return null;
    }
  }

  function closeDetail() {
    const panel = root.document && root.document.getElementById("client-orders-detail");
    const overlay = root.document && root.document.getElementById("client-orders-detail-overlay");
    if (panel) panel.hidden = true;
    if (overlay) overlay.hidden = true;
  }

  function toggleNotifications() {
    if (!root.document || !isRaiosModule()) return;
    const list = root.document.getElementById("mdr-orders-notification-list");
    const bell = root.document.getElementById("mdr-orders-bell");
    if (!list || !bell) return;
    list.hidden = !list.hidden;
    bell.setAttribute("aria-expanded", list.hidden ? "false" : "true");
  }

  function bindEvents() {
    if (eventsBound || !root.document || !root.document.addEventListener) return;
    eventsBound = true;
    root.document.addEventListener("click", function (event) {
      const target = event.target;
      const orderTarget = target && target.closest ? target.closest("[data-client-order-id]") : null;
      if (orderTarget && orderTarget.closest && orderTarget.closest("#cv-pedidos")) {
        event.preventDefault();
        openOrder(orderTarget.getAttribute("data-client-order-id"));
        return;
      }
      if (target && target.closest && target.closest("#mdr-orders-bell")) toggleNotifications();
      else if (target && target.closest && (target.closest("#client-orders-detail-close") || target.closest("#client-orders-detail-overlay"))) closeDetail();
    });
    root.document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") closeDetail();
      const row = event.target && event.target.closest ? event.target.closest(".client-order-row") : null;
      if (row && (event.key === "Enter" || event.key === " ")) { event.preventDefault(); openOrder(row.getAttribute("data-client-order-id")); }
    });
  }

  async function load() {
    bindEvents();
    if (!isRaiosModule()) { currentOrders = []; render([]); return []; }
    try {
      currentOrders = await root.api("/api/whatsapp/orders");
      applyFilters();
      return currentOrders;
    } catch (error) {
      currentOrders = [];
      render([]);
      const summary = root.document && root.document.getElementById("client-orders-summary");
      if (summary) summary.textContent = error.message;
      return [];
    }
  }

  return { ORDER_STATES, PENDING_STATES, escapeHtml, filterOrders, pendingOrders, clientOrders, buildClientDetailHtml, render, readFilters, applyFilters, openOrder, closeDetail, toggleNotifications, load };
});
