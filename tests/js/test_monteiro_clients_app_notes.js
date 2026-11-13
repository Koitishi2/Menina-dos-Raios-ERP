"use strict";

const assert = require("assert");
const fs = require("fs");
const vm = require("vm");

const source = fs.readFileSync("backend/static/index.html", "utf8");
const start = source.indexOf("function palClientIdentity(");
const end = source.indexOf("async function ensurePaladarClientFilterOptions(", start);
assert(start > 0 && end > start);
for (const id of ["pal-cli-note-total", "pal-cli-note-count", "pal-cli-note-report-panel",
  "pal-cli-note-report-client", "pal-cli-note-report-pdf", "pal-cli-note-report-result"]) {
  assert(source.includes(`id="${id}"`), `${id} is present in Clientes`);
}
const context = vm.createContext({ Map });
vm.runInContext(source.slice(start, end), context);

const sales = [{ client: "PALADAR BASE", num_vendas: 2, qty_total: 10, total: 150, ultima_compra: "2026-11-03" }];
const notes = [
  { client: "Paladar  Base", note_count: 3, note_total: 200, last_note_date: "2026-11-05", missing_price_count: 1 },
  { client: "Só APP", note_count: 1, note_total: 30, last_note_date: "2026-11-06", missing_price_count: 0 },
];
const rows = context.palMergeClientRows(sales, notes, "");
assert.equal(rows.length, 2, "one row for the same customer in both sources");
const paladar = rows.find(row => row.client === "PALADAR BASE");
assert.equal(paladar.total, 150, "sale total stays separate");
assert.equal(paladar.note_total, 200, "APP note total stays separate");
assert.equal(paladar.note_count, 3);
assert.equal(paladar.note_missing, 1);
assert.equal(rows.find(row => row.client === "Só APP").num_vendas, 0);
assert.equal(context.palMergeClientRows(sales, notes, "só app").length, 1);
assert.equal(context.palMergeClientRows(sales, notes, "paladar").length, 1);
const spellingVariants = context.palMergeClientRows([
  ...sales, { client: "Paladar  Base", num_vendas: 1, total: 90 },
], notes, "");
assert.equal(spellingVariants.length, 3, "existing sale reports with different names stay individually accurate");
assert.equal(spellingVariants.reduce((sum, row) => sum + row.total, 0), 240);
assert.equal(spellingVariants.reduce((sum, row) => sum + row.note_total, 0), 230);

const mainScript = source.match(/<script>([\s\S]*?)<\/script>/);
assert(mainScript);
new vm.Script(mainScript[1]);
console.log("Monteiro Clientes merges APP note identities without mixing totals: OK");
