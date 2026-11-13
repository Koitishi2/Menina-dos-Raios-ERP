"use strict";

const assert = require("assert");
const fs = require("fs");
const vm = require("vm");

const html = fs.readFileSync("backend/static/index.html", "utf8");
const start = html.indexOf("var _appNoteReportReady={};");
const end = html.indexOf("function renderAppNotes(", start);
assert(start > 0 && end > start);
for (const id of ["app-notes-tab-report", "app-notes-report-pane", "app-note-report-client",
  "app-note-report-mode", "app-note-report-month", "app-note-report-start",
  "app-note-report-end", "app-note-report-pdf", "app-note-report-result"]) {
  assert(html.includes(`id="${id}"`), `${id} exists`);
}
for (const id of ["pal-cli-note-report-client", "pal-cli-note-report-mode", "pal-cli-note-report-month",
  "pal-cli-note-report-start", "pal-cli-note-report-end", "pal-cli-note-report-pdf", "pal-cli-note-report-result"]) {
  assert(html.includes(`id="${id}"`), `${id} exists in Monteiro Clientes`);
}

const nodes = {
  "app-note-report-client": { value: "Loja HGR" },
  "app-note-report-mode": { value: "monthly" },
  "app-note-report-month": { value: "2026-11" },
  "app-note-report-start": { value: "2026-11-03" },
  "app-note-report-end": { value: "2026-11-20" },
  "app-note-report-monthly": { hidden: false },
  "app-note-report-custom": { hidden: true },
  "app-note-report-custom-end": { hidden: true },
  "app-note-report-pdf": { disabled: true, textContent: "Baixar PDF A4" },
  "app-note-report-result": { innerHTML: "" },
  "pal-cli-note-report-client": { value: "Loja HGR" },
  "pal-cli-note-report-mode": { value: "monthly" },
  "pal-cli-note-report-month": { value: "2026-11" },
  "pal-cli-note-report-start": { value: "2026-11-03" },
  "pal-cli-note-report-end": { value: "2026-11-20" },
  "pal-cli-note-report-monthly": { hidden: false },
  "pal-cli-note-report-custom": { hidden: true },
  "pal-cli-note-report-custom-end": { hidden: true },
  "pal-cli-note-report-pdf": { disabled: true, textContent: "Baixar PDF A4" },
  "pal-cli-note-report-result": { innerHTML: "" },
};
let requested;
const report = {
  client: "Loja HGR", note_count: 2, product_count: 1, total: 55,
  missing_price_count: 0,
  products: [{ product: "ABACAXI", quantity: 5, unit: "UN", unit_price: 11, total: 55 }],
  days: [{ date: "20/11/2026", notes: 2, total: 55 }],
};
const context = vm.createContext({
  document: { getElementById: id => nodes[id] },
  URLSearchParams,
  api: async path => { requested = path; return report; },
  appNoteQty: value => String(value), appNoteMoney: value => `R$ ${value}`,
  admEsc: value => String(value), toast: () => {},
});
vm.runInContext(html.slice(start, end), context);

(async () => {
  assert.equal(context.appNoteReportParams().get("month"), "2026-11");
  await context.loadAppNoteReport();
  assert(requested.includes("month=2026-11"));
  assert(nodes["app-note-report-result"].innerHTML.includes("ABACAXI"));
  assert(nodes["app-note-report-result"].innerHTML.includes("R$ 55"));
  assert.equal(nodes["app-note-report-pdf"].disabled, false);
  await context.loadAppNoteReport("pal-cli-note-report");
  assert(nodes["pal-cli-note-report-result"].innerHTML.includes("ABACAXI"));
  assert.equal(nodes["pal-cli-note-report-pdf"].disabled, false);
  assert.equal(nodes["app-note-report-pdf"].disabled, false);

  nodes["app-note-report-mode"].value = "custom";
  context.appNoteReportModeChanged();
  assert.equal(nodes["app-note-report-monthly"].hidden, true);
  assert.equal(nodes["app-note-report-custom"].hidden, false);
  assert.equal(nodes["app-note-report-custom-end"].hidden, false);
  assert.equal(nodes["app-note-report-pdf"].disabled, true);
  assert.equal(context.appNoteReportParams().get("start"), "2026-11-03");
  assert.equal(context.appNoteReportParams().get("end"), "2026-11-20");
  await context.loadAppNoteReport();
  assert(requested.includes("start=2026-11-03"));

  report.missing_price_count = 1;
  await context.loadAppNoteReport();
  assert.equal(nodes["app-note-report-pdf"].disabled, true);
  assert(nodes["app-note-report-result"].innerHTML.includes("sem preço"));
  console.log("Notas APP report filters and totals: OK");
})().catch(error => { console.error(error); process.exitCode = 1; });
