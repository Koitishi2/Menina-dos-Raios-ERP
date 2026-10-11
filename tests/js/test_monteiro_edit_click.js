"use strict";

const assert = require("assert");
const fs = require("fs");
const vm = require("vm");

const html = fs.readFileSync("backend/static/index.html", "utf8");
const whitelist = html.match(/const safeInlineNames = (\[[\s\S]*?\]);/);
assert(whitelist, "inline handler sanitizer is present");
const allowed = vm.runInNewContext(whitelist[1]);
assert(allowed.includes("editPaladarGroup"), "full-edit handler survives HTML sanitization");
const checkStart = html.indexOf("function isSafeInlineHandler(");
const checkEnd = html.indexOf("function sanitizeHtml(", checkStart);
assert(checkStart >= 0 && checkEnd > checkStart);
const context = vm.createContext({ safeInlineNames: allowed });
vm.runInContext(html.slice(checkStart, checkEnd), context);
assert(context.isSafeInlineHandler("editPaladarGroup('group1')"), "sanitizer accepts the row action");
assert(html.includes('onclick="editPaladarGroup(\\\''), "Monteiro row invokes full edit");
assert(html.includes('async function editPaladarGroup(groupId){'), "full-edit function exists");
console.log("Monteiro full-edit button binding: OK");
