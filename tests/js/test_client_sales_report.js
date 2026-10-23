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
assert(html.includes("downloadClientSalesPDF(d,clientSalesReportState.mode==='internal')"));
assert(html.includes("Evolução mensal por produto"));
assert(html.includes("products_without_sales"));
assert(html.includes("products_outside_clients"));
assert(html.includes("showAllClientSalesReportClients()"));
assert(html.includes("Nenhuma para os clientes selecionados."));
assert(html.includes("['Produto','Qtd.','Receita','Parte','Vs. mes']"));
assert(html.includes("['Data','Cliente','Produto','Qtd.','Total']"));
assert(html.includes('.client-sales-report-picker label input[type="checkbox"]{flex:0 0 16px;width:16px!important'));
assert(html.includes("<span>'+esc(value)+'</span></label>"));

const reportStart = html.indexOf("const clientSalesReportState=");
const reportEnd = html.indexOf("function switchClientView(view){", reportStart);
const reportCode = html.slice(reportStart, reportEnd);
assert(reportCode.includes("ORC_COMPANIES[activeCompany]"));
assert(reportCode.includes("company.logo_print||company.logo"));
assert(!reportCode.includes("nf_number"), "client report must not show invoice numbers");
console.log("Client sales report UI: OK");
