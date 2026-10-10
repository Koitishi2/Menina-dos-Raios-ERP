"use strict";

const assert = require("assert");
const fs = require("fs");
const vm = require("vm");

const html = fs.readFileSync("backend/static/index.html", "utf8");
const start = html.indexOf("<script>");
const end = html.indexOf("</script>", start);
assert(start >= 0 && end > start);
new vm.Script(html.slice(start + 8, end));

for (const id of ["cv-btn-relatorio", "cv-relatorio", "csr-start", "csr-end", "csr-clients-options", "csr-products-options", "csr-pdf"]) {
  assert(html.includes(`id="${id}"`), `${id} is present`);
}
assert(html.includes("selectVisibleClientSalesReportProducts()"));
assert(html.includes("downloadClientSalesPortfolioPDF(d)"));

const reportStart = html.indexOf("const clientSalesReportState=");
const reportEnd = html.indexOf("function switchClientView(view){", reportStart);
const reportCode = html.slice(reportStart, reportEnd);
assert(reportCode.includes("ORC_COMPANIES[activeCompany]"));
assert(reportCode.includes("company.logo_print||company.logo"));
assert(!reportCode.includes("nf_number"), "client report must not show invoice numbers");
console.log("Client sales report UI: OK");
