"use strict";

const assert = require("assert");
const fs = require("fs");
const vm = require("vm");

const html = fs.readFileSync("backend/static/index.html", "utf8");
const limits = html.match(/const MAX_SALE_ITEMS=(\d+);\s*const MAX_MONTEIRO_ITEMS=(\d+);/);
assert(limits, "sale and Monteiro limits are defined");
assert.strictEqual(Number(limits[1]), 50);
assert.strictEqual(Number(limits[2]), 50);
assert(html.includes("Produtos (até 50 itens)"));

const addStart = html.indexOf("function addSaleLine(prod,qty,price){");
const addEnd = html.indexOf("function removeSaleLine(id){", addStart);
const monteiroStart = html.indexOf("function addPaladarItem(){");
const monteiroEnd = html.indexOf("function autoFillPrice(", monteiroStart);
assert(addStart >= 0 && addEnd > addStart && monteiroStart >= 0 && monteiroEnd > monteiroStart);
assert(html.slice(addStart, addEnd).includes("currentLines>=MAX_SALE_ITEMS"));
assert(html.slice(monteiroStart, monteiroEnd).includes("q.length >= MAX_MONTEIRO_ITEMS"));

const context = vm.createContext({});
vm.runInContext(html.slice(limits.index, limits.index + limits[0].length), context);
assert.strictEqual(vm.runInContext("MAX_SALE_ITEMS", context), 50);
assert.strictEqual(vm.runInContext("MAX_MONTEIRO_ITEMS", context), 50);
console.log("Sale item limits: OK");
