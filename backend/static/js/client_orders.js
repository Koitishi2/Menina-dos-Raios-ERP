(function (root, factory) {
  const api = factory(root);
  if (typeof module === "object" && module.exports) module.exports = api;
  root.ClientOrdersFoundation = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function (root) {
  "use strict";
  const ORDER_STATES = ["rascunho", "aguardando_confirmacao", "aguardando_aprovacao", "aprovado", "cancelado", "convertido_em_venda", "erro", "duplicado_suspeito"];
  const PENDING_STATES = ["rascunho", "aguardando_confirmacao", "aguardando_aprovacao"];
  const APPROVED_STATES = ["aprovado", "convertido_em_venda"];
  const REJECTED_STATES = ["cancelado"];
  const PRODUCT_LABELS = { MAC_PCT: "Macaxeira com casca", MAC_VACUO: "Macaxeira a vacuo", ALHO_250G: "Alho descascado 250g", ALHO_KG: "Alho descascado 1kg", MAC_CHIPS: "Macaxeira chips", PRE_COZIDA: "Macaxeira pre-cozida" };
  let currentOrders = [];
  let eventsBound = false;
  let activeOrderId = "";
  let activeOrdersView = "pending";

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

  function dateParts(value) {
    const text = String(value || "").trim();
    const match = text.match(/^(\d{4})-(\d{2})-(\d{2})/);
    if (!match) return null;
    return { year: match[1], month: match[1] + "-" + match[2], date: new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3])) };
  }

  function isoWeekKey(date) {
    if (!(date instanceof Date) || Number.isNaN(date.getTime())) return "";
    const day = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
    const weekday = day.getUTCDay() || 7;
    day.setUTCDate(day.getUTCDate() + 4 - weekday);
    const yearStart = new Date(Date.UTC(day.getUTCFullYear(), 0, 1));
    const week = Math.ceil((((day - yearStart) / 86400000) + 1) / 7);
    return day.getUTCFullYear() + "-W" + String(week).padStart(2, "0");
  }

  function matchesPeriod(order, active) {
    if (!active || !active.period) return true;
    const parts = dateParts(order.created_at);
    if (!parts) return false;
    const mode = active.periodMode || "month";
    if (mode === "year") return parts.year === String(active.period);
    if (mode === "week") return isoWeekKey(parts.date) === String(active.period);
    return parts.month === String(active.period);
  }

  function filterOrders(orders, filters) {
    const source = Array.isArray(orders) ? orders : [];
    const active = filters || {};
    return source.filter(function (order) {
      if (active.view && !matchesView(order, active.view)) return false;
      if (active.client && !String(order.client_name || order.client || "").toLowerCase().includes(String(active.client).toLowerCase())) return false;
      if (active.company && order.company_key !== active.company && order.company !== active.company) return false;
      if (!matchesPeriod(order, active)) return false;
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

  function approvedOrders(orders) {
    return (Array.isArray(orders) ? orders : []).filter(function (order) { return APPROVED_STATES.indexOf(order.status) >= 0; });
  }

  function rejectedOrders(orders) {
    return (Array.isArray(orders) ? orders : []).filter(function (order) { return REJECTED_STATES.indexOf(order.status) >= 0; });
  }

  function matchesView(order, view) {
    const status = order && order.status;
    if (view === "approved") return APPROVED_STATES.indexOf(status) >= 0;
    if (view === "rejected") return REJECTED_STATES.indexOf(status) >= 0;
    return PENDING_STATES.indexOf(status) >= 0;
  }

  function viewLabel(view) {
    if (view === "approved") return "aprovados";
    if (view === "rejected") return "recusados";
    return "pendentes";
  }

  function emptyViewLabel(view) {
    if (view === "approved") return "aprovado";
    if (view === "rejected") return "recusado";
    return "pendente";
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

  function renderViewTabs(orders) {
    if (!root.document) return;
    const pending = pendingOrders(orders).length;
    const approved = approvedOrders(orders).length;
    const rejected = rejectedOrders(orders).length;
    const nodes = {
      pending: root.document.getElementById("client-orders-count-pending"),
      approved: root.document.getElementById("client-orders-count-approved"),
      rejected: root.document.getElementById("client-orders-count-rejected")
    };
    if (nodes.pending) nodes.pending.textContent = String(pending);
    if (nodes.approved) nodes.approved.textContent = String(approved);
    if (nodes.rejected) nodes.rejected.textContent = String(rejected);
    if (root.document.querySelectorAll) {
      Array.prototype.forEach.call(root.document.querySelectorAll("[data-client-orders-view]"), function (button) {
        button.classList.toggle("is-active", button.getAttribute("data-client-orders-view") === activeOrdersView);
      });
    }
  }

  function render(orders) {
    const body = root.document && root.document.getElementById("client-orders-list");
    const summary = root.document && root.document.getElementById("client-orders-summary");
    if (!body) return;
    const items = Array.isArray(orders) ? orders : [];
    if (summary) summary.textContent = items.length + " pedido(s) " + viewLabel(activeOrdersView);
    renderViewTabs(currentOrders);
    renderNotifications(currentOrders);
    if (!items.length) {
      body.innerHTML = '<div class="client-orders-empty"><strong>Nenhum pedido ' + escapeHtml(emptyViewLabel(activeOrdersView)) + '</strong><span>Use as sub-abas para consultar pedidos aprovados e recusados sem misturar com a fila pendente.</span></div>';
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
    return { view: activeOrdersView, client: value("client-orders-client"), periodMode: value("client-orders-period-mode") || "month", period: value("client-orders-period"), status: value("client-orders-status"), origin: value("client-orders-origin"), withDamage: checked("client-orders-damage"), aboveMaximum: checked("client-orders-maximum"), suspectedDuplicate: checked("client-orders-duplicate"), awaitingApproval: checked("client-orders-approval") };
  }

  function applyFilters() { render(filterOrders(currentOrders, readFilters())); }

  function setOrderView(view) {
    activeOrdersView = view === "approved" || view === "rejected" ? view : "pending";
    const status = root.document && root.document.getElementById("client-orders-status");
    if (status) status.value = "";
    applyFilters();
  }

  function updatePeriodInput() {
    const mode = root.document && root.document.getElementById("client-orders-period-mode");
    const input = root.document && root.document.getElementById("client-orders-period");
    if (!input) return;
    const value = mode ? mode.value : "month";
    input.type = value === "week" ? "week" : value === "year" ? "number" : "month";
    input.placeholder = value === "year" ? "Ano" : "";
    if (value === "year") {
      input.min = "2020";
      input.max = "2100";
      input.step = "1";
    } else {
      input.removeAttribute && input.removeAttribute("min");
      input.removeAttribute && input.removeAttribute("max");
      input.removeAttribute && input.removeAttribute("step");
    }
  }

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

  function actionStatusHtml(message, type) {
    if (!message) return "";
    return '<div class="client-orders-action-status ' + escapeHtml(type || "") + '">' + escapeHtml(message) + '</div>';
  }

  function pendingActionsHtml(detail) {
    if (!detail) return "";
    const pendingButtons = detail.status === "aguardando_aprovacao"
      ? '<button type="button" class="client-orders-action is-primary" data-client-order-action="confirm" data-client-order-id="' + escapeHtml(detail.id) + '">Aprovar pedido</button>'
        + '<button type="button" class="client-orders-action is-danger" data-client-order-action="reject" data-client-order-id="' + escapeHtml(detail.id) + '">Recusar pedido</button>'
      : "";
    return '<section class="client-orders-detail-section client-orders-actions" data-client-orders-actions><h4>Ações do pedido</h4>'
      + '<div class="client-orders-action-row">'
      + pendingButtons
      + '<button type="button" class="client-orders-action is-danger is-outline" data-client-order-action="delete" data-client-order-id="' + escapeHtml(detail.id) + '">Remover pedido</button>'
      + '</div><small>Aprovar, recusar ou remover não cria venda, não baixa estoque e não envia WhatsApp.</small></section>';
  }

  function newOrderItemRowHtml(index) {
    const options = Object.keys(PRODUCT_LABELS).map(function (key) {
      return '<option value="' + escapeHtml(key) + '">' + escapeHtml(PRODUCT_LABELS[key]) + '</option>';
    }).join("");
    return '<div class="client-orders-new-item" data-client-orders-new-item>'
      + '<label>Produto<select name="product_key" required>' + options + '</select></label>'
      + '<label>Quantidade<input name="quantity" type="number" min="0.001" step="0.001" ' + (index === 0 ? "required" : "") + '></label>'
      + '<label>Avaria<input name="damage" type="number" min="0" step="0.001" value="0"></label>'
      + (index > 0 ? '<button type="button" class="client-orders-remove-item" data-client-orders-remove-item aria-label="Remover item">×</button>' : '')
      + '</div>';
  }

  function newOrderFormHtml(client) {
    const safeClient = client || {};
    return '<section class="client-orders-detail-section client-orders-new-order"><h4>Novo pedido deste cliente</h4>'
      + '<form data-client-new-order-form data-client-id="' + escapeHtml(safeClient.client_id || "") + '">'
      + '<div class="client-orders-new-items" data-client-orders-new-items>' + newOrderItemRowHtml(0) + '</div>'
      + '<div class="client-orders-action-row"><button type="button" class="client-orders-action" data-client-orders-add-item>Adicionar item</button><button type="submit" class="client-orders-action is-primary">Criar rascunho</button></div>'
      + '<small>Inclua macaxeira, alho ou outros itens do catálogo no mesmo rascunho. Nada será enviado pelo WhatsApp.</small>'
      + '</form></section>';
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
      + pendingActionsHtml(detail)
      + '<section class="client-orders-detail-section"><h4>Itens e informações solicitadas</h4>' + orderItemsHtml(detail.items) + '</section>'
      + '<section class="client-orders-detail-section"><h4>Histórico e processamento</h4>' + orderHistoryHtml(detail.history) + '</section>'
      + newOrderFormHtml(detail);
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
    activeOrderId = String(order.id || "");
    try {
      const detail = await root.api("/api/whatsapp/orders/" + encodeURIComponent(order.id));
      body.innerHTML = buildClientDetailHtml(detail, clientOrders(currentOrders, order.client_id), detail);
      activeOrderId = String(detail.id || order.id || "");
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
    activeOrderId = "";
  }

  function updateLocalOrder(order) {
    if (!order || !order.id) return;
    const index = currentOrders.findIndex(function (item) { return String(item.id) === String(order.id); });
    const summary = {
      id: order.id,
      client_id: order.client_id,
      client_name: order.client_name,
      client_phone: order.client_phone,
      created_at: order.created_at,
      company_key: order.company_key,
      status: order.status,
      total: order.total,
      block_reason: order.block_reason,
      withDamage: !!order.with_damage,
      aboveMaximum: !!order.above_maximum
    };
    if (index >= 0) currentOrders[index] = Object.assign({}, currentOrders[index], summary);
    else currentOrders.unshift(summary);
    applyFilters();
  }

  function removeLocalOrder(orderId) {
    currentOrders = currentOrders.filter(function (item) { return String(item.id) !== String(orderId); });
    applyFilters();
    renderNotifications(currentOrders);
  }

  async function requestJson(path, method, payload) {
    const options = { method: method, headers: { "Content-Type": "application/json" } };
    if (payload !== undefined) options.body = JSON.stringify(payload || {});
    return root.api(path, options);
  }

  async function postJson(path, payload) {
    return requestJson(path, "POST", payload || {});
  }

  async function deleteJson(path) {
    return requestJson(path, "DELETE");
  }

  function setActionStatus(message, type) {
    const section = root.document && root.document.querySelector && root.document.querySelector("[data-client-orders-actions]");
    if (!section) return;
    const existing = section.querySelector(".client-orders-action-status");
    if (existing) existing.remove();
    section.insertAdjacentHTML("beforeend", actionStatusHtml(message, type));
  }

  async function runOrderAction(action, orderId) {
    if (!orderId) return null;
    const body = root.document && root.document.getElementById("client-orders-detail-body");
    try {
      setActionStatus("Processando...", "");
      let result;
      if (action === "confirm") {
        result = await postJson("/api/whatsapp/orders/" + encodeURIComponent(orderId) + "/confirm", {});
      } else if (action === "reject") {
        const reason = root.prompt ? root.prompt("Informe o motivo da recusa do pedido:") : "";
        if (!String(reason || "").trim()) {
          setActionStatus("Informe o motivo para recusar.", "is-error");
          return null;
        }
        result = await postJson("/api/whatsapp/orders/" + encodeURIComponent(orderId) + "/reject", { reason: reason });
      } else if (action === "delete") {
        if (root.confirm && !root.confirm("Remover este pedido da lista? Esta ação não cria venda, não baixa estoque e não envia WhatsApp.")) return null;
        result = await deleteJson("/api/whatsapp/orders/" + encodeURIComponent(orderId));
      } else {
        return null;
      }
      if (action === "delete" && result && result.ok) {
        removeLocalOrder(orderId);
        closeDetail();
        return result.order || { id: orderId, removed: true };
      }
      if (result && result.order) {
        updateLocalOrder(result.order);
        if (body) body.innerHTML = buildClientDetailHtml(result.order, clientOrders(currentOrders, result.order.client_id), result.order);
        setActionStatus(result.changed === false ? "Pedido já estava atualizado." : "Pedido atualizado.", "is-success");
        return result.order;
      }
    } catch (error) {
      const message = error && error.message ? error.message : "Falha ao atualizar pedido.";
      setActionStatus(message.indexOf("409") >= 0 ? "Pedido já foi alterado. Reabra para ver o estado atual." : message, "is-error");
    }
    return null;
  }

  async function submitNewOrder(form) {
    const body = root.document && root.document.getElementById("client-orders-detail-body");
    const rows = Array.prototype.slice.call(form.querySelectorAll("[data-client-orders-new-item]"));
    const items = rows.map(function (row) {
      const product = row.querySelector("[name='product_key']");
      const quantity = row.querySelector("[name='quantity']");
      const damage = row.querySelector("[name='damage']");
      return {
        product_key: product ? product.value : "",
        quantity: quantity ? quantity.value : "",
        damage: damage ? (damage.value || "0") : "0"
      };
    }).filter(function (item) { return String(item.quantity || "").trim(); });
    const payload = {
      client_id: form.getAttribute("data-client-id"),
      items: items
    };
    if (!payload.items.length) {
      form.insertAdjacentHTML("beforeend", actionStatusHtml("Informe ao menos um item com quantidade.", "is-error"));
      return null;
    }
    if (root.confirm && !root.confirm("Criar um novo rascunho de pedido para este cliente?")) return null;
    try {
      const button = form.querySelector("button[type='submit']");
      if (button) button.disabled = true;
      const result = await postJson("/api/whatsapp/orders/new-for-client", payload);
      if (result && result.order) {
        updateLocalOrder(result.order);
        activeOrderId = String(result.order.id || "");
        if (body) body.innerHTML = buildClientDetailHtml(result.order, clientOrders(currentOrders, result.order.client_id), result.order);
        return result.order;
      }
    } catch (error) {
      form.insertAdjacentHTML("beforeend", actionStatusHtml(error.message || "Falha ao criar rascunho.", "is-error"));
    } finally {
      const button = form.querySelector("button[type='submit']");
      if (button) button.disabled = false;
    }
    return null;
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
      if (target && target.closest && target.closest("[data-client-order-action]")) {
        const button = target.closest("[data-client-order-action]");
        event.preventDefault();
        runOrderAction(button.getAttribute("data-client-order-action"), button.getAttribute("data-client-order-id") || activeOrderId);
        return;
      }
      if (target && target.closest && target.closest("[data-client-orders-view]")) {
        const button = target.closest("[data-client-orders-view]");
        event.preventDefault();
        setOrderView(button.getAttribute("data-client-orders-view"));
        return;
      }
      const orderTarget = target && target.closest ? target.closest("[data-client-order-id]") : null;
      if (orderTarget && orderTarget.closest && orderTarget.closest("#cv-pedidos")) {
        event.preventDefault();
        openOrder(orderTarget.getAttribute("data-client-order-id"));
        return;
      }
      if (target && target.closest && target.closest("#mdr-orders-bell")) toggleNotifications();
      else if (target && target.closest && (target.closest("#client-orders-detail-close") || target.closest("#client-orders-detail-overlay"))) closeDetail();
      else if (target && target.closest && target.closest("[data-client-orders-add-item]")) {
        const form = target.closest("form");
        const list = form && form.querySelector("[data-client-orders-new-items]");
        if (list) list.insertAdjacentHTML("beforeend", newOrderItemRowHtml(list.querySelectorAll("[data-client-orders-new-item]").length));
      } else if (target && target.closest && target.closest("[data-client-orders-remove-item]")) {
        const row = target.closest("[data-client-orders-new-item]");
        if (row) row.remove();
      }
    });
    root.document.addEventListener("submit", function (event) {
      const form = event.target && event.target.closest ? event.target.closest("[data-client-new-order-form]") : null;
      if (!form) return;
      event.preventDefault();
      submitNewOrder(form);
    });
    root.document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") closeDetail();
      const row = event.target && event.target.closest ? event.target.closest(".client-order-row") : null;
      if (row && (event.key === "Enter" || event.key === " ")) { event.preventDefault(); openOrder(row.getAttribute("data-client-order-id")); }
    });
  }

  async function load() {
    bindEvents();
    updatePeriodInput();
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

  return { ORDER_STATES, PENDING_STATES, APPROVED_STATES, REJECTED_STATES, escapeHtml, filterOrders, pendingOrders, approvedOrders, rejectedOrders, clientOrders, buildClientDetailHtml, render, readFilters, applyFilters, setOrderView, updatePeriodInput, openOrder, closeDetail, toggleNotifications, runOrderAction, submitNewOrder, load };
});
