"use strict";

const assert = require("assert");
const fs = require("fs");
const vm = require("vm");

const html = fs.readFileSync("backend/static/index.html", "utf8");
const start = html.indexOf("function queuePaladarInvoiceFiles(");
const end = html.indexOf("async function openPaladarSaleModal(){", start);
assert(start >= 0 && end > start, "Invoice selection queue helpers are present");

const handlers = {};
function element() {
  return {
    dataset: {}, style: {}, children: [], textContent: "", value: "",
    replaceChildren() { this.children = []; },
    appendChild(child) { this.children.push(child); },
    append(...children) { this.children.push(...children); },
    addEventListener(name, listener) { handlers[this.id + ":" + name] = listener; },
    setAttribute(name, value) { this[name] = value; },
    contains() { return true; }
  };
}
const input = element();
input.id = "pal-sale-invoice";
const list = element();
list.id = "pal-sale-invoice-list";
const toasts = [];
const context = vm.createContext({
  window: { _palPendingInvoiceFiles: [], _palEditingGroup: null },
  document: {
    getElementById(id) {
      return id === "pal-sale-invoice" ? input : id === "pal-sale-invoice-list" ? list : null;
    },
    createElement() { return element(); }
  },
  toast(message) { toasts.push(message); },
  Array,
  Set,
  Number,
  String
});
vm.runInContext(html.slice(start, end), context);
context.bindPaladarInvoiceQueue();

function select(files) {
  input.files = files;
  handlers["pal-sale-invoice:change"].call(input);
}
select([{ name: "nota-a.pdf", size: 100, lastModified: 1 }]);
assert.deepStrictEqual(Array.from(context.window._palPendingInvoiceFiles, file => file.name), ["nota-a.pdf"]);
assert.strictEqual(input.value, "", "clear picker after collecting selection so another file can be added");
assert(String(list.children[1].children[0].textContent).includes("nota-a.pdf"), "show picked file in queue");

select([{ name: "nota-b.xml", size: 200, lastModified: 2 }]);
assert.deepStrictEqual(Array.from(context.window._palPendingInvoiceFiles, file => file.name), ["nota-a.pdf", "nota-b.xml"]);
select([{ name: "nota-b.xml", size: 200, lastModified: 2 }]);
assert.strictEqual(context.window._palPendingInvoiceFiles.length, 2, "do not add the same file twice");

context.window._palEditingGroup = { invoiceCount: 4 };
select([{ name: "nota-c.jpg", size: 300, lastModified: 3 }]);
assert.strictEqual(context.window._palPendingInvoiceFiles.length, 2, "reject overflow without losing files already selected");
assert(toasts.some(message => message.includes("limite é 5")), "explain the five-file limit");

const removeButton = element();
removeButton.dataset.removePendingInvoice = "0";
list.contains = () => true;
handlers["pal-sale-invoice-list:click"]({ target: { closest() { return removeButton; } } });
assert.deepStrictEqual(Array.from(context.window._palPendingInvoiceFiles, file => file.name), ["nota-b.xml"]);
console.log("Monteiro invoice selection queue: OK");
