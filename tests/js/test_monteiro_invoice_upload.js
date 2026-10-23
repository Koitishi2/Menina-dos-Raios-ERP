"use strict";

const assert = require("assert");
const fs = require("fs");
const vm = require("vm");

const html = fs.readFileSync("backend/static/index.html", "utf8");
const start = html.indexOf("async function loadPaladarSales(){");
const end = html.indexOf("function togglePalGroup(sg){", start);
assert(start >= 0 && end > start, "Monteiro sales table source is present");

const listeners = {};
const wrap = {
  dataset: {},
  innerHTML: "",
  addEventListener(name, listener) { listeners[name] = listener; },
  contains() { return true; }
};
let uploaded = false;
let uploadCalls = 0;
const toasts = [];
const sale = {
  sale_group: "group1", saledate: "2026-10-07", client: "Cliente de teste",
  nf_number: "123", total_group: 10, items: [], invoices: []
};
const context = vm.createContext({
  document: { getElementById(id) { return id === "pal-lanc-table-wrap" ? wrap : null; } },
  window: { _palExpandedGroups: {} },
  _palLancView: "lancamentos",
  getPalPeriod() { return "monthly"; },
  getPalFilterMonth() { return "10"; },
  getPalFilterYear() { return "2026"; },
  async api() { return [{ ...sale, invoices: uploaded ? [{ id: "one", name: "123.pdf" }, { id: "two", name: "456.pdf" }] : [] }]; },
  async uploadPaladarInvoice(groupId, files) {
    assert.strictEqual(groupId, "group1");
    assert.deepStrictEqual(Array.from(files, file => file.name), ["123.pdf", "456.pdf"]);
    uploadCalls++;
    uploaded = true;
  },
  toast(message) { toasts.push(message); }
});
vm.runInContext(html.slice(start, end), context);

function selectedFile(status) {
  const label = { classList: { add() {}, remove() {} }, parentElement: { querySelector() { return status; } } };
  return {
    files: [{ name: "123.pdf" }, { name: "456.pdf" }],
    parentElement: label,
    value: "123.pdf",
    disabled: false,
    closest(selector) { return selector === ".pal-invoice-upload" ? label : this; },
    getAttribute(name) { return name === "data-current-count" ? "0" : "group1"; }
  };
}

(async () => {
  await context.loadPaladarSales();
  assert(wrap.innerHTML.includes('type="file"'), "Anexar has a native file input");
  assert(wrap.innerHTML.includes(" multiple "), "Anexar accepts multiple files at once");
  assert(wrap.innerHTML.includes('data-pal-invoice-upload="group1"'));
  assert(!wrap.innerHTML.includes("promptUploadPaladarInvoice"));
  const status = { hidden: true, textContent: "", classList: { add() {}, remove() {} } };
  const input = selectedFile(status);
  await listeners.change({ target: input });
  assert.strictEqual(uploadCalls, 1);
  assert.strictEqual(input.value, "", "same file can be selected again");
  assert(toasts.includes("2 arquivo(s) anexado(s)!"));
  assert(wrap.innerHTML.includes("Ver (2)"), "table shows a viewer for uploaded files");
  assert(wrap.innerHTML.includes("Anexar (2/5)"), "table shows remaining attachment capacity");
  console.log("Monteiro invoice upload JS: OK");
})().catch(error => { console.error(error); process.exitCode = 1; });
