"use strict";

const assert = require("assert");
const fs = require("fs");
const vm = require("vm");

const html = fs.readFileSync("backend/static/index.html", "utf8");
const start = html.indexOf("function bolTodayIso(){");
const end = html.indexOf("// Inicializa o picker do Boletos", start);
assert(start >= 0 && end > start, "local boleto date helper exists");

class LocalDate extends Date {
  getFullYear() { return 2026; }
  getMonth() { return 9; }
  getDate() { return 22; }
  toISOString() { return "2026-10-23T00:30:00.000Z"; }
}

const context = vm.createContext({ Date: LocalDate });
vm.runInContext(html.slice(start, end), context);
assert.strictEqual(context.bolTodayIso(), "2026-10-22", "filter uses local day, not next UTC day");
assert(html.includes("const todayStr = bolTodayIso();"), "today filter uses local date helper");
console.log("Boleto local date filter: OK");
