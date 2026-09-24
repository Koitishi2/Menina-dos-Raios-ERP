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
    if (summary) summary.textContent = items.length + " pedido(s) do WhatsApp";
    if (!items.length) { body.innerHTML = '<div class="client-orders-empty"><strong>Nenhum pedido recebido</strong><span>Os pedidos aparecem aqui assim que o cliente escolhe um produto no questionário. Nenhuma venda é criada automaticamente.</span></div>'; return; }
    body.innerHTML = '<div class="client-orders-table"><table><thead><tr><th>ID</th><th>Cliente</th><th>Data</th><th>Origem</th><th>Total</th><th>Status</th><th>Bloqueio</th><th>Ação</th></tr></thead><tbody>'
      + items.map(function (item) { const warning = item.status === "duplicado_suspeito" || item.status === "erro"; const id = escapeHtml(item.id || ""); return '<tr data-order-id="' + id + '" onclick="ClientOrdersFoundation.openOrder(\'' + id + '\')"><td>' + escapeHtml(String(item.id || "").slice(0, 8)) + '</td><td>' + escapeHtml(item.client_name || "Cliente") + '</td><td>' + escapeHtml(item.created_at || "") + '</td><td>WhatsApp</td><td>' + escapeHtml(item.total || "0") + '</td><td><span class="client-order-status ' + (warning ? "is-warning" : "") + '">' + escapeHtml(String(item.status || "").replace(/_/g, " ")) + '</span></td><td>' + escapeHtml(item.block_reason || "-") + '</td><td><button type="button" class="client-order-view" onclick="event.stopPropagation();ClientOrdersFoundation.openOrder(\'' + id + '\')">Ver</button></td></tr>'; }).join("")
      + '</tbody></table></div>';
  }

  function field(label, value) { return '<div class="client-order-detail-field"><span>' + escapeHtml(label) + '</span><strong>' + escapeHtml(value == null || value === "" ? "-" : value) + '</strong></div>'; }
  function orderScore(order) { try { const memory = JSON.parse(order.calculation_memory || "{}"); return memory.order_score == null ? "-" : memory.order_score + "/100"; } catch (_error) { return "-"; } }
  function ensureOrderDetailUi() {
    const doc = root.document;
    if (!doc || !doc.createElement || !doc.body) return null;
    let modal = doc.getElementById("client-order-detail-modal");
    if (modal) return modal;
    const style = doc.createElement("style");
    style.id = "client-order-detail-styles";
    style.textContent = ".client-orders-table tbody tr{cursor:pointer}.client-orders-table tbody tr:hover,.client-orders-table tbody tr:focus-within{background:var(--g50)}.client-order-view{background:transparent;border:1px solid var(--border);color:var(--g800);cursor:pointer;font-size:10px;font-weight:700;min-height:30px;padding:5px 9px}.client-order-modal{align-items:center;background:rgba(15,23,42,.62);display:flex;inset:0;justify-content:center;padding:18px;position:fixed;z-index:1300}.client-order-modal[hidden]{display:none}.client-order-modal-panel{background:var(--card);border:1px solid var(--border);max-height:min(780px,92vh);max-width:920px;overflow:auto;width:100%}.client-order-modal-head{align-items:center;background:var(--card);border-bottom:1px solid var(--border);display:flex;justify-content:space-between;padding:14px 16px;position:sticky;top:0;z-index:1}.client-order-modal-head strong{color:var(--g800);display:block;font-size:15px}.client-order-modal-head span{color:var(--muted);display:block;font-size:10px;margin-top:3px}.client-order-close{align-items:center;background:transparent;border:1px solid var(--border);color:var(--g800);cursor:pointer;display:inline-flex;font-size:22px;height:34px;justify-content:center;padding:0;width:34px}.client-order-detail-body{display:grid;gap:14px;padding:16px}.client-order-detail-grid{display:grid;gap:9px;grid-template-columns:repeat(4,minmax(0,1fr))}.client-order-detail-field{border-bottom:1px solid var(--border);min-width:0;padding:7px 0}.client-order-detail-field span{color:var(--muted);display:block;font-size:9px;font-weight:700;text-transform:uppercase}.client-order-detail-field strong{color:var(--g800);display:block;font-size:12px;margin-top:4px;overflow-wrap:anywhere}.client-order-section h4{color:var(--g800);font-size:11px;margin:0 0 7px;text-transform:uppercase}.client-order-items{border:1px solid var(--border);border-collapse:collapse;width:100%}.client-order-items th,.client-order-items td{border-bottom:1px solid var(--border);font-size:10px;padding:8px;text-align:left}.client-order-thread{display:grid;gap:7px}.client-order-message{border-left:3px solid var(--border);padding:7px 9px}.client-order-message.is-sent{border-left-color:#1683b8}.client-order-message strong{color:var(--g800);display:block;font-size:10px}.client-order-message p{color:var(--text);font-size:11px;margin:4px 0 0;white-space:pre-wrap}.client-order-loading,.client-order-error{color:var(--muted);font-size:12px;padding:24px;text-align:center}@media(max-width:620px){.client-order-modal{align-items:flex-end;padding:0}.client-order-modal-panel{max-height:94vh}.client-order-detail-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}";
    doc.head.appendChild(style);
    modal = doc.createElement("div");
    modal.id = "client-order-detail-modal";
    modal.className = "client-order-modal";
    modal.hidden = true;
    modal.setAttribute("role", "dialog");
    modal.setAttribute("aria-modal", "true");
    modal.setAttribute("aria-labelledby", "client-order-detail-title");
    modal.innerHTML = '<div class="client-order-modal-panel"><div class="client-order-modal-head"><div><strong id="client-order-detail-title">Detalhes do pedido</strong><span id="client-order-detail-subtitle"></span></div><button type="button" class="client-order-close" aria-label="Fechar detalhes" title="Fechar">&times;</button></div><div id="client-order-detail-body" class="client-order-detail-body"></div></div>';
    modal.querySelector(".client-order-close").addEventListener("click", closeOrder);
    modal.addEventListener("click", function (event) { if (event.target === modal) closeOrder(); });
    doc.body.appendChild(modal);
    return modal;
  }
  function renderOrderDetail(order) {
    const body = root.document.getElementById("client-order-detail-body");
    const subtitle = root.document.getElementById("client-order-detail-subtitle");
    if (!body) return;
    if (subtitle) subtitle.textContent = (order.client_name || "Cliente") + " · " + String(order.id || "").slice(0, 8);
    const items = Array.isArray(order.items) ? order.items : [];
    const messages = Array.isArray(order.messages) ? order.messages : [];
    body.innerHTML = '<div class="client-order-detail-grid">' + field("Status", String(order.status || "").replace(/_/g, " ")) + field("Etapa da conversa", String(order.conversation && order.conversation.status || "").replace(/_/g, " ")) + field("Pontuação", orderScore(order)) + field("Total", order.total || "0") + field("Criado em", order.created_at) + field("Atualizado em", order.updated_at) + field("Confirmado em", order.confirmed_at) + field("Bloqueio", order.block_reason) + '</div>'
      + '<section class="client-order-section"><h4>Itens solicitados</h4><div class="client-orders-table"><table class="client-order-items"><thead><tr><th>Produto</th><th>Quantidade</th><th>Avaria</th><th>Unidade</th><th>Total</th></tr></thead><tbody>' + (items.length ? items.map(function (item) { return '<tr><td>' + escapeHtml(item.product_name || item.product_key) + '</td><td>' + escapeHtml(item.requested_quantity || "-") + '</td><td>' + escapeHtml(item.confirmed_damage || "0") + '</td><td>' + escapeHtml(item.unit || "-") + '</td><td>' + escapeHtml(item.total || "0") + '</td></tr>'; }).join("") : '<tr><td colspan="5">Produto ainda não informado.</td></tr>') + '</tbody></table></div></section>'
      + '<section class="client-order-section"><h4>Questionário no WhatsApp</h4><div class="client-order-thread">' + (messages.length ? messages.map(function (message) { const sent = message.direction === "enviada"; return '<div class="client-order-message ' + (sent ? "is-sent" : "") + '"><strong>' + (sent ? "Bot" : "Cliente") + ' · ' + escapeHtml(message.status || "") + '</strong><p>' + escapeHtml(message.body || "") + '</p></div>'; }).join("") : '<div class="client-order-message"><p>Nenhuma mensagem registrada.</p></div>') + '</div></section>';
  }

  async function openOrder(orderId) {
    const modal = ensureOrderDetailUi() || root.document && root.document.getElementById("client-order-detail-modal");
    const body = root.document && root.document.getElementById("client-order-detail-body");
    if (!modal || !body) return;
    modal.hidden = false; body.innerHTML = '<div class="client-order-loading">Carregando pedido...</div>';
    try { renderOrderDetail(await root.api("/api/whatsapp/orders/" + encodeURIComponent(orderId))); }
    catch (error) { body.innerHTML = '<div class="client-order-error">' + escapeHtml(error.message || "Não foi possível abrir o pedido.") + '</div>'; }
  }
  function closeOrder() { const modal = root.document && root.document.getElementById("client-order-detail-modal"); if (modal) modal.hidden = true; }

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

  return { ORDER_STATES, filterOrders, render, renderOrderDetail, ensureOrderDetailUi, readFilters, applyFilters, load, openOrder, closeOrder };
});
