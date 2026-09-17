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

assert.deepStrictEqual(orders.ORDER_STATES, [
  "rascunho", "aguardando_confirmacao", "aguardando_aprovacao", "aprovado",
  "cancelado", "convertido_em_venda", "erro", "duplicado_suspeito"
]);

const sampleOrders = [
  { client: "Ana", company: "raios", status: "aguardando_aprovacao", origin: "whatsapp", withDamage: true },
  { client: "Bruno", company: "estrada", status: "duplicado_suspeito", origin: "manual", aboveMaximum: true }
];
assert.deepStrictEqual(orders.filterOrders(sampleOrders, { awaitingApproval: true }), [sampleOrders[0]]);
assert.deepStrictEqual(orders.filterOrders(sampleOrders, { suspectedDuplicate: true }), [sampleOrders[1]]);
assert.deepStrictEqual(orders.filterOrders(sampleOrders, { company: "raios", withDamage: true }), [sampleOrders[0]]);

testVisibleAsyncFailureWithoutRetry()
  .then(testClientDetailsWithoutConversation)
  .then(() => console.log("client WhatsApp/orders foundation JS: OK"))
  .catch((error) => { console.error(error); process.exit(1); });
