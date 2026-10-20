"use strict";

const assert = require("assert");
const fs = require("fs");
const vm = require("vm");

const html = fs.readFileSync("backend/static/index.html", "utf8");
const helpersStart = html.indexOf("function appNoteMoney(");
const actionStart = html.indexOf("function appNoteActionButton(");
const actionEnd = html.indexOf("function handleAppNoteAction(", actionStart);
const renderStart = html.indexOf("function renderAppNotes(");
const renderEnd = html.indexOf("function openAppNoteDetail(", renderStart);
assert(helpersStart >= 0 && actionStart > helpersStart && actionEnd > actionStart && renderStart >= 0 && renderEnd > renderStart);

const nodes = { "app-notes-kpis": { innerHTML: "" }, "app-notes-wrap": { innerHTML: "" },
  "pal-view-notasapp": { style: { display: "block" } } };
const context = vm.createContext({
  document: { getElementById(id) { return nodes[id]; } },
  session: { role: "editor" },
  _appNotesStatus: "pending",
  _appNotes: [{ id: "note-1", client: "Cliente", note_date: "07/10/2026", total: 160,
    items: [
      { product: "Produto", quantity: 1, weight: 1, unit: "KG", unit_price: 10,
        price_provided: true, quantity_provided: true },
      { product: "Macaxeira", quantity: 0, weight: 30, unit: "KG", unit_price: 5,
        price_provided: true, quantity_provided: false }
    ], submissions: [] }],
  appNoteMoney(v) { return `R$ ${v}`; },
  appNoteQty(v) { return String(v); },
  appNoteHasPrice() { return true; },
  appNoteUnitPrice(i) { return i.unit_price; },
  appNoteAttr(v) { return String(v); },
  appNoteSubmissionSummary() { return ""; },
  admEsc(v) { return String(v); },
  admDate(v) { return String(v || ""); }
});
vm.runInContext(html.slice(helpersStart, actionStart) + html.slice(actionStart, actionEnd) + html.slice(renderStart, renderEnd), context);

const weightOnly = { quantity: 0, quantity_provided: 0, weight: 30, unit: "KG" };
assert.strictEqual(context.appNoteEffectiveQuantity(weightOnly), 30, "weight is shown as quantity for KG-only notes");
assert.strictEqual(context.appNoteQuantityDisplay(weightOnly), "30", "weight quantity is displayed without its unit suffix");
assert.strictEqual(context.appNoteUnitDisplay(weightOnly.unit), "kg", "unit is shown in its own column");

context.renderAppNotes({ count: 1, total: 160 });
for (const action of ["edit", "status", "delete"]) {
  assert(nodes["app-notes-wrap"].innerHTML.includes(`data-app-note-action="${action}"`), `${action} visible to editor`);
}
assert(nodes["app-notes-wrap"].innerHTML.includes('class="app-note-items-table"'));
assert(nodes["app-notes-wrap"].innerHTML.includes('data-label="Subtotal"'));
assert(nodes["app-notes-wrap"].innerHTML.includes('data-label="Quantidade" style="padding:11px 12px;text-align:center">30'));
assert(nodes["app-notes-wrap"].innerHTML.includes('data-label="Unidade"'));
assert(!nodes["app-notes-wrap"].innerHTML.includes('data-label="Medida"'));

context.session.role = "viewer";
context.renderAppNotes({ count: 1, total: 160 });
for (const action of ["edit", "status", "delete"]) {
  assert(!nodes["app-notes-wrap"].innerHTML.includes(`data-app-note-action="${action}"`), `${action} hidden from viewer`);
}
assert(html.includes(".app-note-items-table td::before"), "small-screen labels present");

const readOnlyStart = html.indexOf("function isMobileReadOnlyAllowed(");
const readOnlyEnd = html.indexOf("function isMobileMutatingElement(", readOnlyStart);
const allowStart = html.indexOf("function mobileAppNoteActionAllowed(");
const allowEnd = html.indexOf("function applyMobileReadOnlyUI(", allowStart);
assert(readOnlyStart >= 0 && readOnlyEnd > readOnlyStart && allowStart >= 0 && allowEnd > allowStart);
context.isMobileView = () => true;
context.mobileNormalizeText = v => String(v || "").toLowerCase();
vm.runInContext(html.slice(readOnlyStart, readOnlyEnd) + html.slice(allowStart, allowEnd), context);
const noteAction = {
  closest(selector) { return selector === '#pal-view-notasapp [data-app-note-action]' ? this : null; },
  getAttribute() { return ""; }, textContent: "Editar"
};
context.session.role = "editor";
assert(context.isMobileReadOnlyAllowed(noteAction), "editor note action survives mobile read-only filter");
assert(context.mobileAppNoteActionAllowed("saveAppNote"), "editor can save from mobile note modal");
assert(!context.mobileAppNoteActionAllowed("deletePaladarSale"), "other mobile edits stay protected");
context.session.role = "viewer";
assert(!context.mobileAppNoteActionAllowed("saveAppNote"), "viewer stays read-only");
console.log("Monteiro APP notes permissions and responsive markup: OK");
