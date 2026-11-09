const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '..', 'backend', 'static', 'index.html'), 'utf8');
const start = html.indexOf('function openAppNoteModal(');
const end = html.indexOf('async function deleteAppNote(', start);
assert.ok(start >= 0 && end > start);

const fields = {
  product: {value: 'ABACAXI'}, quantity: {value: '5'},
  weight: {value: '5'}, unit: {value: 'UN'}, price: {value: '11,00'},
};
const row = {
  dataset: {originalProduct: 'ABACAXI', originalPrice: '10', originalOverride: '0'},
  querySelector: selector => fields[selector.match(/"([a-z]+)"/)[1]],
};
const elements = {
  'app-note-id': {value: 'note-1'},
  'app-note-edit-client': {value: 'Cliente'},
  'app-note-edit-date': {value: '09/11/2026'},
  'app-note-edit-total': {textContent: ''},
};
let inputHandler;
let request;
const context = {
  document: {
    getElementById: id => elements[id],
    querySelectorAll: () => [row],
    addEventListener: (event, handler) => {if (event === 'input') inputHandler = handler;},
  },
  appNoteMoney: value => `R$ ${Number(value).toFixed(2).replace('.', ',')}`,
  api: async (_url, options) => {request = JSON.parse(options.body);},
  closeAppNoteModal: () => {}, toast: () => {},
  refreshAppNotesNotifications: async () => {}, loadAppNotes: () => {},
};
vm.createContext(context);
vm.runInContext(html.slice(start, end), context);
inputHandler({target: {closest: () => row, getAttribute: () => 'price'}});
assert.equal(elements['app-note-edit-total'].textContent, 'Total calculado: R$ 55,00');
context.saveAppNote().then(() => {
  assert.equal(request.items[0].product, 'ABACAXI');
  assert.equal(request.items[0].quantity, 5);
  assert.equal(request.items[0].weight, 5);
  assert.equal(request.items[0].unit, 'UN');
  assert.equal(request.items[0].unit_price, 11);
  assert.equal(request.items[0].price_override, true);
  console.log('app note editor: OK');
}).catch(error => {console.error(error); process.exitCode = 1;});
