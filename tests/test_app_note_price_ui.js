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
  remove: () => { rows.splice(rows.indexOf(row), 1); },
};
const rows = [row];
const elements = {
  'app-note-id': {value: 'note-1'},
  'app-note-edit-client': {value: 'Cliente'},
  'app-note-edit-date': {value: '09/11/2026'},
  'app-note-edit-total': {textContent: ''},
  'app-note-modal': {style: {}},
  'app-note-modal-title': {textContent: ''},
  'app-note-save-button': {textContent: '', disabled: false},
  'app-note-new-merge-wrap': {hidden: true},
  'app-note-new-merge': {innerHTML: '', value: ''},
  'app-note-new-external-id': {value: ''},
  'app-note-edit-list': {innerHTML: ''},
};
let inputHandler;
let clickHandler;
let request;
let requestPath;
const context = {
  document: {
    getElementById: id => elements[id],
    querySelectorAll: () => rows,
    addEventListener: (event, handler) => {
      if (event === 'input') inputHandler = handler;
      if (event === 'click') clickHandler = handler;
    },
  },
  appNoteMoney: value => `R$ ${Number(value).toFixed(2).replace('.', ',')}`,
  appNoteAttr: value => String(value || ''), appNoteHasPrice: () => false,
  appNoteQty: value => String(value),
  api: async (url, options) => {requestPath = url; request = JSON.parse(options.body); return {note: {items: []}};},
  session: {role: 'admin'}, window: {crypto: {randomUUID: () => 'erp-web-test'}},
  switchPaladarTab: () => {},
  closeAppNoteModal: () => {}, toast: () => {},
  refreshAppNotesNotifications: async () => {}, loadAppNotes: () => {},
};
vm.createContext(context);
vm.runInContext(html.slice(start, end), context);
inputHandler({target: {closest: () => row, getAttribute: () => 'price'}});
assert.equal(elements['app-note-edit-total'].textContent, 'Total calculado: R$ 55,00');
context.saveAppNote().then(() => {
  assert.equal(requestPath, '/api/app-notes/note-1');
  assert.equal(request.items[0].product, 'ABACAXI');
  assert.equal(request.items[0].quantity, 5);
  assert.equal(request.items[0].weight, 5);
  assert.equal(request.items[0].unit, 'UN');
  assert.equal(request.items[0].unit_price, 11);
  assert.equal(request.items[0].price_override, true);
  let prevented = false;
  const removeButton = {closest: selector => selector.includes('data-app-note-remove-item') ? removeButton : row};
  clickHandler({target: removeButton, preventDefault: () => {prevented = true;}});
  assert(prevented);
  assert.equal(rows.length, 0, 'Remover elimina a linha antes de salvar');
  assert.equal(elements['app-note-edit-total'].textContent, 'Preço final calculado pelo servidor ao salvar.');
  elements['app-note-edit-client'].focus = () => {};
  context.loadAppNoteProductOptions = () => {};
  context.openNewAppNoteModal();
  assert.equal(elements['app-note-modal-title'].textContent, 'Lançar Nota APP');
  assert.equal(elements['app-note-new-external-id'].value, 'erp-web-test');
  assert(elements['app-note-edit-list'].innerHTML.includes('data-app-note-remove-item'));
  elements['app-note-edit-client'].value = 'Cliente';
  fields.product.value = 'ABACAXI';
  row.dataset.originalProduct = '';
  row.dataset.originalPrice = '';
  rows.push(row);
  return context.saveAppNote();
}).then(() => {
  assert.equal(requestPath, '/api/app-notes');
  assert.equal(request.external_id, 'erp-web-test');
  assert.equal(request.items[0].price_override, true);
  console.log('app note editor: OK');
}).catch(error => {console.error(error); process.exitCode = 1;});
