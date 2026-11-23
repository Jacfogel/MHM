import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFile} from 'node:fs/promises';

const source = await readFile(new URL('./whatsapp-enrollment.js', import.meta.url), 'utf8');
function node(tag = '') {
  return {tag, children: [], value: '', checked: false, hidden: false, disabled: false,
    textContent: '', listeners: {}, append(...items) {this.children.push(...items);},
    setAttribute() {}, addEventListener(event, callback) {this.listeners[event] = callback;}};
}
async function screen(info) {
  const calls = []; const states = [];
  const parent = node();
  const window = {};
  vm.runInNewContext(source, {window, document: {createElement: node, createTextNode: text => text},
    fetch: async (_url, options) => {
      const data = options.body ? JSON.parse(options.body) : null;
      calls.push(data);
      return Response.json(data?.action === 'start' ? {token: 'a'.repeat(32), sender: '+15555550100'}
        : data?.action === 'connect' ? {connected: true} : info);
    }});
  await window.MHMWhatsApp.mount(parent, state => states.push(state));
  const box = parent.children[0];
  return {calls, states, box, phone: box.children[1].children[0],
    consent: box.children[2].children[0], start: box.children[3], verify: box.children[4], status: box.children[6]};
}

test('trial accounts cannot begin WhatsApp enrollment', async () => {
  const view = await screen({available: true, eligible: false, trial: true});
  assert.equal(view.start.disabled, true);
  assert.match(view.status.textContent, /WhatsApp plan/);
  assert.equal(view.calls.length, 1);
});

test('paid user sends proof and consent without changing delivery automatically', async () => {
  const view = await screen({available: true, eligible: true, phone: ''});
  view.phone.value = '+15555550199'; view.consent.checked = true;
  await view.start.listeners.click();
  assert.match(view.status.textContent, /LINK a{32}/);
  assert.equal(view.verify.hidden, false);
  await view.verify.listeners.click();
  assert.deepEqual(view.calls[2], {action: 'connect', phone: '+15555550199', consent: true, token: 'a'.repeat(32)});
  assert.equal(view.states.at(-1).connected, true);
  assert.match(view.status.textContent, /Choose WhatsApp delivery and save/);
  assert.equal(view.calls.some(call => call?.channel), false);
});

test('changing the phone invalidates the displayed connection code', async () => {
  const view = await screen({available: true, eligible: true});
  view.phone.value = '+15555550199'; view.consent.checked = true;
  await view.start.listeners.click(); view.phone.value = '+15555550188';
  await view.verify.listeners.click();
  assert.match(view.status.textContent, /phone changed/);
  assert.equal(view.calls.length, 2);
});
