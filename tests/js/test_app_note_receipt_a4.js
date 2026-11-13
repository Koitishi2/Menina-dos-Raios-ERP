"use strict";

const assert = require("assert");
const fs = require("fs");
const vm = require("vm");

const source = fs.readFileSync("backend/static/index.html", "utf8");
const mainScript = source.match(/<script>([\s\S]*?)<\/script>/);
assert(mainScript, "main page script must exist");
assert(mainScript[1].includes("async function setAppNoteStatus("), "receipt markup must not close the main page script");
new vm.Script(mainScript[1], { filename: "backend/static/index.html" });
const start = source.indexOf("function appNoteReceiptHtml(");
const end = source.indexOf("async function setAppNoteStatus(", start);
assert(start > 0 && end > start);
let written = "";
const popup = { document: { open() {}, write(html) { written = html; }, close() {} }, focus() {} };
const context = vm.createContext({
  _appNotes: [],
  appNoteQuantityDisplay: item => String(item.quantity),
  appNoteUnitDisplay: unit => unit,
  appNoteHasPrice: () => true,
  appNoteUnitPrice: item => item.unit_price,
  appNoteMoney: value => Number(value || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" }),
  appNoteSubmissionSummary: () => "Vendedor · 10/11/2026",
  admEsc: value => String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;"),
  window: { open: () => popup },
  toast: () => {},
});
vm.runInContext(source.slice(start, end), context);

function note(count) {
  return { id: "nota-teste", client: "Cliente HGR", note_date: "10/11/2026", status: "completed", total: count * 10,
    items: Array.from({ length: count }, (_, index) => ({ product: `PRODUTO ${String(index + 1).padStart(3, "0")}`,
      quantity: 1, weight: 1, unit: "UN", unit_price: 10, price_from_catalog: index % 2 === 0 })) };
}

for (const count of [1, 38, 39, 50, 100]) {
  const html = context.appNoteReceiptHtml(note(count));
  assert(html.includes("@page{size:A4 portrait;margin:0}"));
  assert(html.includes("beforeprint"));
  assert(html.includes("Total do pedido"));
  assert(html.includes('<th class="num">Valor un.</th><th class="num">Subtotal</th>'));
  assert(html.includes('font-variant-numeric:tabular-nums'));
  assert(html.includes('<div class="sign">Responsável pelo recebimento</div><div class="sign">Entregue por</div>'));
  assert(html.includes(`PRODUTO ${String(count).padStart(3, "0")}`));
  assert.equal((html.match(/class="sheet"/g) || []).length, 1);
  assert.equal((html.match(/<tr><td class="product">/g) || []).length, count);
  assert.equal(html.includes('class="item-tables two'), count > 38);
  if (process.env.APP_NOTE_RECEIPT_QA_DIR && [1, 50, 100].includes(count)) {
    fs.mkdirSync(process.env.APP_NOTE_RECEIPT_QA_DIR, { recursive: true });
    fs.writeFileSync(`${process.env.APP_NOTE_RECEIPT_QA_DIR}/recibo-${count}.html`, html);
  }
}
if (process.env.APP_NOTE_RECEIPT_QA_DIR) {
  const sample = {
    id: "22ca5872-6b54-4b3a-8784-fe728284c842",
    client: "PALADAR DISTRITO", note_date: "06/11/2026", status: "pending", total: 16161.4,
    items: [
      ["ABÓBORA", 400, "KG", 5], ["ALFACE", 10, "MAÇO", 6],
      ["BATATA DOCE", 600, "KG", 5], ["BATATA INGLESA", 208, "KG", 7],
      ["CENOURA", 500, "KG", 8], ["CHEIRO VERDE", 40, "MAÇO", 2],
      ["COUVE", 30, "MAÇO", 2.5], ["LARANJA", 6, "SACO", 80],
      ["MACAXEIRA", 300, "KG", 5], ["MAÇÃ", 19, "CX", 180],
      ["PIMENTÃO", 5, "KG", 15], ["REPOLHO", 2.2, "KG", 7],
    ].map(([product, weight, unit, unit_price]) => ({ product, quantity: weight, weight, unit, unit_price, price_from_catalog: true })),
  };
  fs.writeFileSync(`${process.env.APP_NOTE_RECEIPT_QA_DIR}/recibo-comparacao.html`, context.appNoteReceiptHtml(sample));
}
context._appNotes = [note(1)];
context.printAppNoteReceipt("nota-teste");
assert(written.includes("Cliente HGR"));
assert(written.includes("PRODUTO 001"));
console.log("Notas APP receipt A4 markup and complete items: OK");
