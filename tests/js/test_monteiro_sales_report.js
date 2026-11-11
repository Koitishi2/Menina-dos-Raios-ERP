"use strict";

const assert = require("assert");
const fs = require("fs");
const vm = require("vm");

const html = fs.readFileSync("backend/static/index.html", "utf8");
const start = html.indexOf("var _palLancReportReady=false;");
const end = html.indexOf("async function uploadPaladarInvoice(", start);
assert(start > 0 && end > start);
for (const id of ["pal-lanc-report-pane", "pal-lanc-list-pane", "pal-lanc-report-client",
  "pal-lanc-report-mode", "pal-lanc-report-month", "pal-lanc-report-start", "pal-lanc-report-end",
  "pal-lanc-report-pdf", "pal-lanc-report-result", "pal-lanc-report-clients"]) {
  assert(html.includes(`id="${id}"`), `${id} exists`);
}
assert(html.includes('data-pal-lanc-view="report"'));

const nodes = {
  "pal-lanc-report-client": { value: "Loja HGR" },
  "pal-lanc-report-mode": { value: "monthly" },
  "pal-lanc-report-month": { value: "2026-11" },
  "pal-lanc-report-start": { value: "2026-11-02" },
  "pal-lanc-report-end": { value: "2026-11-20" },
  "pal-lanc-report-monthly": { hidden: false },
  "pal-lanc-report-custom-start": { hidden: true },
  "pal-lanc-report-custom-end": { hidden: true },
  "pal-lanc-report-pdf": { disabled: true, textContent: "Baixar PDF A4" },
  "pal-lanc-report-result": { innerHTML: "" },
  "pal-lanc-report-clients": { innerHTML: "" },
};
let requested;
let downloadUrl;
let clicked = false;
const report = {
  client: "Loja HGR", sale_count: 2, item_count: 3, total: 79,
  products: [{ product: "ABACAXI", quantity: 5, unit_price: 10, total: 50 }],
  days: [{ date: "2026-11-02", sales: 1, total: 62 }],
  sales: [{ date: "2026-11-02", nf_number: "HGR-001", items: 2, total: 62 }],
};
const context = vm.createContext({
  document: {
    getElementById: id => nodes[id],
    createElement: () => ({ click: () => { clicked = true; }, remove: () => {} }),
    body: { appendChild: () => {} },
  },
  URLSearchParams,
  URL: { createObjectURL: () => "blob:report", revokeObjectURL: () => {} },
  fetch: async url => { downloadUrl = url; return { ok: true, blob: async () => ({ size: 100 }) }; },
  API: "", session: { token: "test-token" }, apiHeaders: headers => headers,
  setTimeout: () => {},
  api: async path => { requested = path; return path.endsWith("/clients") ? { clients: ["Loja HGR"] } : report; },
  admEsc: value => String(value), toast: () => {},
});
vm.runInContext(html.slice(start, end), context);

(async () => {
  assert.equal(context.palLancReportParams().get("month"), "2026-11");
  await context.loadPalLancReportClients();
  assert(nodes["pal-lanc-report-clients"].innerHTML.includes("Loja HGR"));
  await context.loadPalLancReport();
  assert(requested.includes("month=2026-11"));
  assert(nodes["pal-lanc-report-result"].innerHTML.includes("ABACAXI"));
  assert(nodes["pal-lanc-report-result"].innerHTML.includes("HGR-001"));
  assert(nodes["pal-lanc-report-result"].innerHTML.includes("R$"));
  assert.equal(nodes["pal-lanc-report-pdf"].disabled, false);

  nodes["pal-lanc-report-mode"].value = "custom";
  context.palLancReportModeChanged();
  assert.equal(nodes["pal-lanc-report-monthly"].hidden, true);
  assert.equal(nodes["pal-lanc-report-custom-start"].hidden, false);
  assert.equal(nodes["pal-lanc-report-custom-end"].hidden, false);
  assert.equal(nodes["pal-lanc-report-pdf"].disabled, true);
  assert.equal(context.palLancReportParams().get("start"), "2026-11-02");
  assert.equal(context.palLancReportParams().get("end"), "2026-11-20");
  await context.loadPalLancReport();
  assert(requested.includes("start=2026-11-02"));
  assert.equal(nodes["pal-lanc-report-pdf"].disabled, false);
  await context.downloadPalLancReportPdf();
  assert(downloadUrl.includes("/api/monteiro/sales/report/pdf?"));
  assert(clicked);
  assert.equal(nodes["pal-lanc-report-pdf"].disabled, false);

  nodes["pal-lanc-report-client"].value = "";
  context.palLancReportInvalidate();
  assert.equal(nodes["pal-lanc-report-pdf"].disabled, true);
  await context.loadPalLancReport();
  assert(nodes["pal-lanc-report-result"].innerHTML.includes("Escolha um cliente"));
  console.log("Monteiro sales client report filters and totals: OK");
})().catch(error => { console.error(error); process.exitCode = 1; });
