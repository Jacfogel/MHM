import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFile} from 'node:fs/promises';

const phoneSource = await readFile(new URL('./phone-input.js', import.meta.url), 'utf8');
const source = await readFile(new URL('./sms-enrollment.js', import.meta.url), 'utf8');
function node(tag = '') {
  return {tag, children: [], value: '', checked: false, hidden: false, disabled: false,
    textContent: '', listeners: {}, append(...items) {this.children.push(...items);},
    setAttribute() {}, addEventListener(event, callback) {this.listeners[event] = callback;}};
}
async function screen(info) {
  const calls = []; const states = [];
  const parent = node();
  const window = {};
  vm.runInNewContext(phoneSource + '\n' + source, {window, document: {createElement: node, createTextNode: text => text},
    fetch: async (_url, options) => {
      const data = options.body ? JSON.parse(options.body) : null;
      calls.push(data);
      if (!data && info instanceof Response) return info.clone();
      return Response.json(data?.action === 'start' ? {token: 'a'.repeat(32), sender: '+15555550100'}
        : data?.action === 'connect' ? {connected: true} : info);
    }});
  await window.MHMSms.mount(parent, state => states.push(state));
  const box = parent.children[0];
  return {calls, states, box, phone: box.children[1].children[0],
    consent: box.children[2].children[0], start: box.children[3], verify: box.children[4], status: box.children[6]};
}

test('refresh preserves a pending change to a different phone', async () => {
  const view = await screen({available: true, eligible: true, connected: true, phone: '+15555550101'});
  view.phone.value = '+15555550199'; view.consent.checked = true;
  await view.start.listeners.click();
  await view.box.children.at(-1).listeners.click();
  assert.equal(view.verify.hidden, false);
  await view.verify.listeners.click();
  assert.equal(view.calls.at(-1).phone, '+15555550199');
  assert.equal(view.calls.at(-1).token, 'a'.repeat(32));
});

test('trial accounts cannot begin SMS enrollment', async () => {
  const view = await screen({available: true, eligible: false, trial: true});
  assert.equal(view.start.disabled, true);
  assert.match(view.status.textContent, /paid SMS plan/);
  assert.equal(view.calls.length, 1);
});

test('connection refresh shows opt-out and unresolved outcomes without offering replay', async () => {
  const view = await screen({available: true, eligible: true, connected: true, stopped: true,
    delivery: {unresolved_attempts: 2, inbound_needing_review: 1}});
  const recovery = view.box.children[7].textContent;
  assert.match(recovery, /Send START/);
  assert.match(recovery, /3 delivery or reply/);
  assert.match(recovery, /before repeating/);
  assert.match(recovery, /does not confirm delivery/);
  assert.equal(view.verify.hidden, true);
  assert.equal(view.calls.length, 1);
});

test('paid user sends proof and consent without changing delivery automatically', async () => {
  const view = await screen({available: true, eligible: true, phone: ''});
  assert.equal(view.phone.disabled, false);
  assert.equal(view.consent.disabled, false);
  view.phone.value = '+15555550199'; view.consent.checked = true;
  await view.start.listeners.click();
  assert.match(view.status.textContent, /LINK a{32}/);
  assert.equal(view.verify.hidden, false);
  await view.verify.listeners.click();
  assert.deepEqual(view.calls[2], {action: 'connect', phone: '+15555550199', consent: true, token: 'a'.repeat(32)});
  assert.equal(view.states.at(-1).connected, true);
  assert.match(view.status.textContent, /Choose SMS delivery and save/);
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

test('missing enrollment route shows recovery guidance and keeps the request disabled', async () => {
  const view = await screen(Response.json({error: '404: Not Found'}, {status: 404}));
  assert.doesNotMatch(view.status.textContent, /404|Not Found/);
  assert.match(view.status.textContent, /Refresh the connection/);
  assert.equal(view.status.className, 'form-status is-error');
  assert.equal(view.start.disabled, true);
  assert.equal(view.start.dataset.unavailable, 'true');
  await view.box.children.at(-1).listeners.click();
  assert.equal(view.calls.length, 2);
});

 test('phone controls require a subscription and normalize international formatting', async () => {
  const unpaid = await screen({available: true, eligible: false});
  assert.equal(unpaid.phone.disabled, true);
  assert.equal(unpaid.phone.dataset.unavailable, 'true');
  assert.equal(unpaid.consent.disabled, true);
  assert.equal(unpaid.start.disabled, true);
  const view = await screen({available: true, eligible: true});
  view.phone.value = '00 1 (306) 555-0123'; view.consent.checked = true;
  await view.start.listeners.click();
  assert.equal(view.calls[1].phone, '+13065550123');
  assert.equal(view.phone.value, '+13065550123');
  view.phone.value = '+1 (306) 555-0123';
  await view.verify.listeners.click();
  assert.equal(view.calls[2].phone, '+13065550123');
 });
 test('invalid numbers and missing consent never request a connection code', async () => {
  for (const number of ['hello', '3065550123', '+1 306 555 0123 ext 4', '+0123456789', '+123', '+1234567890123456']) {
    const view = await screen({available: true, eligible: true});
    view.phone.value = number; view.consent.checked = true;
    await view.start.listeners.click();
    assert.equal(view.calls.length, 1);
    assert.match(view.status.textContent, /country code/);
  }
  const view = await screen({available: true, eligible: true});
  view.phone.value = '+13065550123';
  await view.start.listeners.click();
  assert.equal(view.calls.length, 1);
  assert.match(view.status.textContent, /consent/);
 });

 test('refresh unlocks phone controls after payment eligibility arrives', async () => {
  const info = {available: true, eligible: false};
  const view = await screen(info);
  assert.equal(view.phone.disabled, true);
  assert.equal(view.consent.disabled, true);
  info.eligible = true;
  await view.box.children.at(-1).listeners.click();
  assert.equal(view.phone.disabled, false);
  assert.equal(view.consent.disabled, false);
  assert.equal(view.start.disabled, false);
  assert.equal(view.phone.dataset.unavailable, 'false');
 });
