"use strict";

const assert = require("assert");
const fs = require("fs");
const vm = require("vm");

const html = fs.readFileSync("backend/static/index.html", "utf8");
const start = html.indexOf("var _palInvoiceViewerUrl=null;");
const end = html.indexOf("// Baixa em ZIP", start);
assert(start >= 0 && end > start, "Monteiro invoice viewer source is present");
assert(html.includes('data-pal-invoice-view="'), "Ver uses the delegated click handler");

const body = {
  innerHTML: "",
  children: [],
  replaceChildren(...children) { this.children = children; },
  appendChild(child) { this.children.push(child); }
};
const download = { hidden: true };
const title = { textContent: "" };
const closeButton = { focus() {} };
const classes = new Set();
const viewer = {
  classList: {
    add(name) { classes.add(name); },
    remove(name) { classes.delete(name); },
    contains(name) { return classes.has(name); }
  },
  querySelector(selector) {
    return {
      ".pal-invoice-viewer-body": body,
      ".pal-invoice-viewer-download": download,
      ".pal-invoice-viewer-title": title,
      ".pal-invoice-viewer-close": closeButton
    }[selector];
  }
};
let completeFetch;
let previewType;
const context = vm.createContext({
  AbortController, Blob,
  URL: {
    createObjectURL(blob) { previewType = blob.type; return "blob:invoice-test"; },
    revokeObjectURL() {}
  },
  window: { _palSaleGroupsById: { group1: { invoice_original_name: "003988.pdf" } } },
  session: { token: "test-token" },
  document: {
    activeElement: { isConnected: true, focus() {} },
    body: { style: { overflow: "" } },
    getElementById(id) { return id === "pal-invoice-viewer" ? viewer : null; },
    createElement(tagName) { return { tagName, setAttribute() {} }; }
  },
  fetch() { return new Promise(resolve => { completeFetch = resolve; }); }
});
vm.runInContext(html.slice(start, end), context);

(async () => {
  const opening = context.openPaladarInvoice("group1");
  assert(classes.has("open"), "viewer opens before the request finishes");
  assert(body.innerHTML.includes("Carregando"));
  completeFetch({ ok: true, blob: async () => new Blob(["pdf"], { type: "application/octet-stream" }) });
  await opening;
  assert.strictEqual(body.children[0].tagName, "iframe");
  assert.strictEqual(previewType, "application/pdf");
  assert.strictEqual(download.hidden, false);

  context.fetch = async () => ({ ok: false, status: 404, json: async () => ({ detail: "Arquivo não encontrado" }) });
  await context.openPaladarInvoice("group1");
  assert(classes.has("open"), "viewer remains open to show the error");
  assert(body.children[0].textContent.includes("Arquivo não encontrado"));
  console.log("Monteiro invoice viewer JS: OK");
})().catch(error => { console.error(error); process.exitCode = 1; });
