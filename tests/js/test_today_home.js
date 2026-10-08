"use strict";

const assert = require("assert");
const fs = require("fs");
const vm = require("vm");

const html = fs.readFileSync("backend/static/index.html", "utf8");
assert(html.includes('id="panel-hoje"'));
assert(html.includes('days_inactive=20'));
assert(html.includes('onclick="switchTab(this,\'hoje\')"'));

const groupStart = html.indexOf("function groupNotasRows(list){");
const groupEnd = html.indexOf("function getPendingCount(){", groupStart);
const todayStart = html.indexOf("function todayDeliverySummary(sales,date){");
const todayEnd = html.indexOf("function renderToday(){", todayStart);
assert(groupStart >= 0 && groupEnd > groupStart && todayStart >= 0 && todayEnd > todayStart);

const context = vm.createContext({ _notaKey: s => s.nf_number ? `${s.client}|${s.sale_date}|${s.nf_number}` : s.id });
vm.runInContext(html.slice(groupStart, groupEnd) + html.slice(todayStart, todayEnd), context);
const sales = [
  { id: 1, sale_date: "2026-10-08", sale_type: "NF", client: "Cliente A", nf_number: "100", delivered: "sim" },
  { id: 2, sale_date: "2026-10-08", sale_type: "NF", client: "Cliente A", nf_number: "100", delivered: null },
  { id: 3, sale_date: "2026-10-08", sale_type: "AVARIA", client: "Cliente B" },
  { id: 4, sale_date: "2026-10-07", sale_type: "NF", client: "Cliente C" },
  { id: 5, sale_date: "2026-10-08", sale_type: "NF", client: "Cliente D", delivered: "sim" }
];
const result = context.todayDeliverySummary(sales, "2026-10-08");
assert.strictEqual(result.groups.length, 2);
assert.strictEqual(result.done, 1);
assert.strictEqual(result.pending.length, 1);
assert.strictEqual(result.pending[0].client, "Cliente A");

const whitelist = html.match(/const safeInlineNames = (\[[\s\S]*?\]);/);
assert(whitelist);
const allowed = vm.runInNewContext(whitelist[1]);
assert(allowed.includes("todayOpen") && allowed.includes("todayOpenConversation"));
console.log("Today home data and navigation: OK");
