"use strict";

const assert = require("assert");
const whatsapp = require("../../backend/static/js/client_whatsapp.js");
const orders = require("../../backend/static/js/client_orders.js");

assert.deepStrictEqual(whatsapp.normalizePhone("(95) 99123-4567"), {
  digits: "5595991234567",
  valid: true,
  e164: "+5595991234567",
  reason: ""
});
assert.strictEqual(whatsapp.normalizePhone("").reason, "Telefone ausente");
assert.strictEqual(whatsapp.normalizePhone("123").valid, false);

const rows = whatsapp.buildRows([
  { id: "1", name: "Cliente A", phone: "95991234567" },
  { id: "2", name: "Cliente B", phone: "" }
]);
assert.strictEqual(rows.length, 2);
assert.strictEqual(rows[0].normalizedPhone, "+5595991234567");
assert.strictEqual(rows[1].phoneValid, false);
assert.strictEqual(rows[0].consent, "desconhecido");
assert.strictEqual(whatsapp.consentLabel("desconhecido"), "Sem autorizacao de envio");
assert.strictEqual(whatsapp.consentLabel("opt_in"), "Consentimento autorizado");

const selection = whatsapp.createSelectionModel();
selection.reset("filter-a");
selection.toggle("1", true, "filter-a");
selection.select([{ client_id: "2", selectable: true }, { client_id: "3", selectable: false }], "filter-a");
assert.deepStrictEqual(selection.values().sort(), ["1", "2"]);
selection.remove("1");
assert.deepStrictEqual(selection.values(), ["2"]);
selection.toggle("4", true, "filter-b");
assert.deepStrictEqual(selection.values(), ["4"], "changing filters must invalidate the old selection");

whatsapp.resetBatchRequest();
const requestA = whatsapp.batchRequestFor("same-payload");
assert.strictEqual(whatsapp.batchRequestFor("same-payload"), requestA);
assert.notStrictEqual(whatsapp.batchRequestFor("changed-payload"), requestA);

const resultRows = whatsapp.batchResultRows({ items: [
  { id: "item-12345678", client_name: "Cliente A", phone_e164: "+5595991234567", status: "enviado", result_code: "ok", sent_at: "2026-09-15T10:00:00" },
  { id: "item-87654321", client_name: "Cliente B", phone_e164: "+5595997654321", status: "falhou", result_detail: "provedor indisponivel" }
] });
assert.strictEqual(resultRows[0].phone, "+5595****4567");
assert.strictEqual(resultRows[0].statusClass, "is-success");
assert.strictEqual(resultRows[1].statusClass, "is-error");
assert.strictEqual(resultRows[1].reason, "provedor indisponivel");

const notice = { style: {}, className: "", innerHTML: "" };
global.document = { getElementById: (id) => id === "client-wa-notice" ? notice : null };
whatsapp.showNotice("Falha assincrona visivel", "error");
assert.strictEqual(notice.style.display, "flex");
assert.ok(notice.innerHTML.includes("Falha assincrona visivel"));
assert.ok(notice.innerHTML.includes("Fechar"));
whatsapp.hideNotice();
assert.strictEqual(notice.style.display, "none");
delete global.document;

async function testVisibleAsyncFailureWithoutRetry() {
  const asyncNotice = { style: {}, className: "", innerHTML: "" };
  let apiCalls = 0;
  global.document = { getElementById: (id) => id === "client-wa-notice" ? asyncNotice : null };
  global.api = async () => { apiCalls += 1; throw new Error("API nao deveria ser chamada sem selecao"); };
  const result = await whatsapp.prepareBatch();
  assert.strictEqual(result, null);
  assert.strictEqual(apiCalls, 0);
  assert.ok(asyncNotice.innerHTML.includes("Selecione ao menos um cliente"));
  delete global.api;
  delete global.document;
}

async function testClientDetailsWithoutConversation() {
  let scrolled = false, focused = false;
  const detail = {
    style: {}, innerHTML: "", textContent: "",
    scrollIntoView: () => { scrolled = true; },
    focus: () => { focused = true; }
  };
  const apiCalls = [];
  global.document = { getElementById: (id) => id === "client-whatsapp-detail" ? detail : null };
  global.api = async (path) => {
    apiCalls.push(path);
    return { client: { id: "1", name: "Cliente A", phone: "+5595991234567" }, consent: null, conversation: null };
  };
  await whatsapp.openConversation("", "1");
  assert.deepStrictEqual(apiCalls, ["/api/clients/1/whatsapp"]);
  assert.strictEqual(detail.style.display, "block");
  assert.ok(detail.innerHTML.includes("Cliente A"));
  assert.ok(detail.innerHTML.includes("Sem autorizacao de envio"));
  assert.ok(detail.innerHTML.includes("Ainda nao existe conversa registrada"));
  assert.ok(detail.innerHTML.includes("nao ha autorizacao registrada"));
  assert.strictEqual(scrolled, true);
  assert.strictEqual(focused, true);
  delete global.api;
  delete global.document;
}

async function testOrderDetailSuccessAndMissingOrder() {
  const nodes = {
    "client-orders-list": { innerHTML: "" },
    "client-orders-summary": { textContent: "" },
    "mdr-orders-bell-badge": { textContent: "", classList: { toggle: () => {} } },
    "mdr-orders-notification-list": { innerHTML: "", hidden: true },
    "mdr-orders-bell": { setAttribute: () => {} },
    "client-orders-detail": { hidden: true },
    "client-orders-detail-overlay": { hidden: true },
    "client-orders-detail-title": { textContent: "" },
    "client-orders-detail-body": { innerHTML: "" },
    "client-orders-count-pending": { textContent: "" },
    "client-orders-count-approved": { textContent: "" },
    "client-orders-count-rejected": { textContent: "" },
    "client-orders-status": { value: "" }
  };
  global.document = {
    body: { classList: { contains: () => false } },
    addEventListener: () => {},
    getElementById: (id) => nodes[id] || null
  };
  global.api = async (path) => {
    if (path === "/api/whatsapp/orders") return [{ id: "order-open", client_id: "client-open", client_name: "Ana", client_phone: "+5595999999999", status: "aguardando_aprovacao", total: "25" }];
    if (path === "/api/whatsapp/orders/order-open") return { id: "order-open", client_id: "client-open", client_name: "Ana", client_phone: "+5595999999999", status: "aguardando_aprovacao", total: "25", items: [], history: [] };
    throw new Error("Pedido nao encontrado.");
  };
  await orders.load();
  const detail = await orders.openOrder("order-open");
  assert.strictEqual(detail.id, "order-open");
  assert.strictEqual(nodes["client-orders-detail"].hidden, false);
  assert.ok(nodes["client-orders-detail-body"].innerHTML.includes("Ana"));
  assert.ok(nodes["client-orders-detail-body"].innerHTML.includes("Nenhum item registrado"));

  global.api = async () => { throw new Error("Pedido nao encontrado."); };
  const missing = await orders.openOrder("order-open");
  assert.strictEqual(missing, null);
  assert.ok(nodes["client-orders-detail-body"].innerHTML.includes("Pedido nao encontrado"));
  delete global.api;
  delete global.document;
}

assert.deepStrictEqual(orders.ORDER_STATES, [
  "rascunho", "aguardando_confirmacao", "aguardando_aprovacao", "aprovado",
  "cancelado", "convertido_em_venda", "erro", "duplicado_suspeito"
]);

const sampleOrders = [
  { client: "Ana", company: "raios", status: "aguardando_aprovacao", origin: "whatsapp", withDamage: true, created_at: "2026-09-27 07:40:49" },
  { client: "Bruno", company: "estrada", status: "duplicado_suspeito", origin: "manual", aboveMaximum: true, created_at: "2026-10-02 08:00:00" },
  { client: "Carla", company: "raios", status: "aprovado", origin: "whatsapp", created_at: "2026-09-28 09:00:00" },
  { client: "Diego", company: "raios", status: "cancelado", origin: "whatsapp", created_at: "2026-09-29 09:00:00" }
];
assert.deepStrictEqual(orders.filterOrders(sampleOrders, { awaitingApproval: true }), [sampleOrders[0]]);
assert.deepStrictEqual(orders.filterOrders(sampleOrders, { suspectedDuplicate: true }), [sampleOrders[1]]);
assert.deepStrictEqual(orders.filterOrders(sampleOrders, { company: "raios", withDamage: true }), [sampleOrders[0]]);
assert.deepStrictEqual(orders.filterOrders(sampleOrders, { periodMode: "month", period: "2026-09" }), [sampleOrders[0], sampleOrders[2], sampleOrders[3]]);
assert.deepStrictEqual(orders.filterOrders(sampleOrders, { periodMode: "year", period: "2026" }), sampleOrders);
assert.deepStrictEqual(orders.filterOrders(sampleOrders, { periodMode: "week", period: "2026-W39" }), [sampleOrders[0]]);
assert.deepStrictEqual(orders.filterOrders(sampleOrders, { periodMode: "week", period: "2026-W40" }), [sampleOrders[1], sampleOrders[2], sampleOrders[3]]);
assert.deepStrictEqual(orders.filterOrders(sampleOrders, { view: "pending" }), [sampleOrders[0]]);
assert.deepStrictEqual(orders.filterOrders(sampleOrders, { view: "approved" }), [sampleOrders[2]]);
assert.deepStrictEqual(orders.filterOrders(sampleOrders, { view: "rejected" }), [sampleOrders[3]]);
assert.deepStrictEqual(orders.approvedOrders(sampleOrders), [sampleOrders[2]]);
assert.deepStrictEqual(orders.rejectedOrders(sampleOrders), [sampleOrders[3]]);

const clientOrderRows = [
  { id: "order-1", client_id: "client-1", client_name: "Ana", status: "aguardando_aprovacao", total: "25" },
  { id: "order-2", client_id: "client-1", client_name: "Ana", status: "aprovado", total: "10" },
  { id: "order-3", client_id: "client-2", client_name: "Bruno", status: "rascunho", total: "5" }
];
assert.deepStrictEqual(orders.clientOrders(clientOrderRows, "client-1"), clientOrderRows.slice(0, 2));
assert.deepStrictEqual(orders.clientOrders(clientOrderRows, "missing"), []);
assert.deepStrictEqual(orders.pendingOrders(clientOrderRows), [clientOrderRows[0], clientOrderRows[2]]);

const emptyOrderHtml = orders.buildClientDetailHtml(
  { client_name: "Cliente sem pedido", client_phone: "+5595999999999" },
  [],
  null
);
assert.ok(emptyOrderHtml.includes("Este cliente ainda não possui pedidos"));
assert.ok(emptyOrderHtml.includes("Cliente sem pedido"));

const orderDetailHtml = orders.buildClientDetailHtml(clientOrderRows[0], clientOrderRows.slice(0, 2), {
  ...clientOrderRows[0],
  client_phone: "+5595912345678",
  created_at: "2026-09-24 10:00:00",
  items: [{ product_key: "MAC_PCT", requested_quantity: "10", confirmed_damage: "1", total: "25" }],
  history: [{ new_status: "aguardando_aprovacao", reason: "confirmacao_whatsapp", changed_by: "cliente" }]
});
assert.ok(orderDetailHtml.includes("Macaxeira com casca"));
assert.ok(orderDetailHtml.includes("confirmacao_whatsapp"));
assert.ok(orderDetailHtml.includes("aguardando aprovacao"));
assert.ok(orderDetailHtml.includes("Aprovar pedido"));
assert.ok(orderDetailHtml.includes("Recusar pedido"));
assert.ok(orderDetailHtml.includes("Novo pedido deste cliente"));
assert.ok(orderDetailHtml.indexOf("Ações do pedido") < orderDetailHtml.indexOf("Itens e informações solicitadas"));
assert.ok(orderDetailHtml.includes("Adicionar item"));
assert.ok(!orderDetailHtml.includes("<script>"));

const ordersSource = require("fs").readFileSync(require("path").join(__dirname, "../../backend/static/js/client_orders.js"), "utf8");
assert.ok(
  ordersSource.indexOf('target.closest("[data-client-order-action]")') < ordersSource.indexOf('target.closest("[data-client-order-id]")'),
  "order action buttons must be handled before generic order opening"
);

async function testOrderActionsUseReadonlyListStateAndPostEndpoints() {
  const nodes = {
    "client-orders-list": { innerHTML: "" },
    "client-orders-summary": { textContent: "" },
    "mdr-orders-bell-badge": { textContent: "", classList: { toggle: () => {} } },
    "mdr-orders-notification-list": { innerHTML: "", hidden: true },
    "mdr-orders-bell": { setAttribute: () => {} },
    "client-orders-detail": { hidden: true },
    "client-orders-detail-overlay": { hidden: true },
    "client-orders-detail-title": { textContent: "" },
    "client-orders-detail-body": { innerHTML: "" }
  };
  nodes["client-orders-detail-body"].querySelector = () => null;
  nodes["client-orders-detail-body"].insertAdjacentHTML = function (_where, html) { this.innerHTML += html; };
  global.document = {
    body: { classList: { contains: () => false } },
    addEventListener: () => {},
    getElementById: (id) => nodes[id] || null,
    querySelectorAll: () => [],
    querySelector: () => ({
      querySelector: () => null,
      insertAdjacentHTML: () => {}
    })
  };
  const calls = [];
  global.api = async (path, opts) => {
    calls.push({ path, opts });
    if (path === "/api/whatsapp/orders") return [{ id: "order-action", client_id: "client-1", client_name: "Ana", status: "aguardando_aprovacao", total: "25" }];
    if (path === "/api/whatsapp/orders/order-action") return { id: "order-action", client_id: "client-1", client_name: "Ana", status: "aguardando_aprovacao", total: "25", items: [], history: [] };
    if (path === "/api/whatsapp/orders/order-action/confirm") return { ok: true, changed: true, order: { id: "order-action", client_id: "client-1", client_name: "Ana", status: "aprovado", total: "25", items: [], history: [] } };
    throw new Error("unexpected api call " + path);
  };
  await orders.load();
  await orders.openOrder("order-action");
  const updated = await orders.runOrderAction("confirm", "order-action");
  assert.strictEqual(updated.status, "aprovado");
  assert.strictEqual(calls[calls.length - 1].path, "/api/whatsapp/orders/order-action/confirm");
  assert.strictEqual(calls[calls.length - 1].opts.method, "POST");
  assert.ok(nodes["client-orders-list"].innerHTML.includes("Nenhum pedido pendente"));
  orders.setOrderView("approved");
  assert.ok(nodes["client-orders-list"].innerHTML.includes("aprovado"));
  assert.ok(!calls.some((call) => String(call.path).includes("/api/whatsapp/send")));
  delete global.api;
  delete global.document;
}

async function testRejectedOrderMovesToRejectedTab() {
  const nodes = {
    "client-orders-list": { innerHTML: "" },
    "client-orders-summary": { textContent: "" },
    "mdr-orders-bell-badge": { textContent: "", classList: { toggle: () => {} } },
    "mdr-orders-notification-list": { innerHTML: "", hidden: true },
    "mdr-orders-bell": { setAttribute: () => {} },
    "client-orders-detail": { hidden: true },
    "client-orders-detail-overlay": { hidden: true },
    "client-orders-detail-title": { textContent: "" },
    "client-orders-detail-body": { innerHTML: "" },
    "client-orders-count-pending": { textContent: "" },
    "client-orders-count-approved": { textContent: "" },
    "client-orders-count-rejected": { textContent: "" },
    "client-orders-status": { value: "" }
  };
  nodes["client-orders-detail-body"].querySelector = () => null;
  nodes["client-orders-detail-body"].insertAdjacentHTML = function (_where, html) { this.innerHTML += html; };
  global.document = {
    body: { classList: { contains: () => false } },
    addEventListener: () => {},
    getElementById: (id) => nodes[id] || null,
    querySelectorAll: () => [],
    querySelector: () => ({
      querySelector: () => null,
      insertAdjacentHTML: () => {}
    })
  };
  global.prompt = () => "cliente recusou";
  global.api = async (path, opts) => {
    if (path === "/api/whatsapp/orders") return [{ id: "order-reject", client_id: "client-2", client_name: "Bruno", status: "aguardando_aprovacao", total: "30" }];
    if (path === "/api/whatsapp/orders/order-reject") return { id: "order-reject", client_id: "client-2", client_name: "Bruno", status: "aguardando_aprovacao", total: "30", items: [], history: [] };
    if (path === "/api/whatsapp/orders/order-reject/reject") {
      assert.strictEqual(opts.method, "POST");
      assert.ok(opts.body.includes("cliente recusou"));
      return { ok: true, changed: true, order: { id: "order-reject", client_id: "client-2", client_name: "Bruno", status: "cancelado", block_reason: "cliente recusou", total: "30", items: [], history: [] } };
    }
    throw new Error("unexpected api call " + path);
  };
  orders.setOrderView("pending");
  await orders.load();
  await orders.openOrder("order-reject");
  const rejected = await orders.runOrderAction("reject", "order-reject");
  assert.strictEqual(rejected.status, "cancelado");
  assert.ok(nodes["client-orders-list"].innerHTML.includes("Nenhum pedido pendente"));
  orders.setOrderView("rejected");
  assert.ok(nodes["client-orders-list"].innerHTML.includes("cancelado"));
  assert.strictEqual(nodes["client-orders-count-rejected"].textContent, "1");
  delete global.api;
  delete global.prompt;
  delete global.document;
}

async function testRemoveOrderDeletesAndClearsList() {
  const nodes = {
    "client-orders-list": { innerHTML: "" },
    "client-orders-summary": { textContent: "" },
    "mdr-orders-bell-badge": { textContent: "", classList: { toggle: () => {} } },
    "mdr-orders-notification-list": { innerHTML: "", hidden: true },
    "mdr-orders-bell": { setAttribute: () => {} },
    "client-orders-detail": { hidden: true },
    "client-orders-detail-overlay": { hidden: true },
    "client-orders-detail-title": { textContent: "" },
    "client-orders-detail-body": { innerHTML: "" },
    "client-orders-count-pending": { textContent: "" },
    "client-orders-count-approved": { textContent: "" },
    "client-orders-count-rejected": { textContent: "" },
    "client-orders-status": { value: "" }
  };
  nodes["client-orders-detail-body"].querySelector = () => null;
  nodes["client-orders-detail-body"].insertAdjacentHTML = function (_where, html) { this.innerHTML += html; };
  global.document = {
    body: { classList: { contains: () => false } },
    addEventListener: () => {},
    getElementById: (id) => nodes[id] || null,
    querySelectorAll: () => [],
    querySelector: () => ({
      querySelector: () => null,
      insertAdjacentHTML: () => {}
    })
  };
  global.confirm = () => true;
  const calls = [];
  global.api = async (path, opts) => {
    calls.push({ path, opts });
    if (path === "/api/whatsapp/orders") return [{ id: "order-delete", client_id: "client-3", client_name: "Clara", status: "aprovado", total: "40" }];
    if (path === "/api/whatsapp/orders/order-delete" && opts && opts.method === "DELETE") {
      assert.strictEqual(opts.method, "DELETE");
      return { ok: true, changed: true, order: { id: "order-delete", status: "aprovado" } };
    }
    if (path === "/api/whatsapp/orders/order-delete") return { id: "order-delete", client_id: "client-3", client_name: "Clara", status: "aprovado", total: "40", items: [], history: [] };
    throw new Error("unexpected api call " + path);
  };
  orders.setOrderView("approved");
  await orders.load();
  await orders.openOrder("order-delete");
  assert.ok(nodes["client-orders-detail-body"].innerHTML.includes("Remover pedido"));
  const removed = await orders.runOrderAction("delete", "order-delete");
  assert.strictEqual(removed.id, "order-delete");
  assert.strictEqual(calls[calls.length - 1].opts.method, "DELETE");
  assert.ok(nodes["client-orders-list"].innerHTML.includes("Nenhum pedido aprovado"));
  assert.strictEqual(nodes["client-orders-count-approved"].textContent, "0");
  assert.ok(!calls.some((call) => String(call.path).includes("/api/whatsapp/send")));
  delete global.api;
  delete global.confirm;
  delete global.document;
}

testVisibleAsyncFailureWithoutRetry()
  .then(testClientDetailsWithoutConversation)
  .then(testOrderDetailSuccessAndMissingOrder)
  .then(testOrderActionsUseReadonlyListStateAndPostEndpoints)
  .then(testRejectedOrderMovesToRejectedTab)
  .then(testRemoveOrderDeletesAndClearsList)
  .then(() => console.log("client WhatsApp/orders foundation JS: OK"))
  .catch((error) => { console.error(error); process.exit(1); });
