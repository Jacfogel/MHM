import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';

const source = await readFile(new URL('./home.js', import.meta.url), 'utf8');

function node(extras = {}) {
  return {
    hidden: true,
    disabled: false,
    textContent: '',
    value: '',
    classList: { add() {}, remove() {}, toggle() {} },
    childNodes: [],
    attributes: {},
    setAttribute(name, value) { this.attributes[name] = value; },
    getAttribute(name) { return this.attributes[name]; },
    removeAttribute(name) { delete this.attributes[name]; },
    addEventListener(type, listener) { this.listeners = this.listeners || {}; this.listeners[type] = listener; },
    append(...children) { this.childNodes.push(...children); },
    replaceChildren(...children) { this.childNodes = children; },
    focus() {},
    ...extras,
  };
}

async function page({ account = { preferred_name: 'River', needs_setup: false, tasks_enabled: true, checkins_enabled: true }, tasks = { tasks: [{ title: 'Drink water', due_date: '2026-09-21', due_time: '09:00' }] }, efforts = { tasks: [] }, energy = null, fetchImpl, random = () => 0, chat = false } = {}) {
  const nodes = new Map([
    ['app-status', node({ hidden: false })],
    ['home-content', node()],
    ['home-name', node()],
    ['home-task-title', node()],
    ['home-task-meta', node()],
    ['home-task-why', node()],
    ['home-task-actions', node()],
    ['home-task-done', node()],
    ['home-task-later', node()],
    ['home-task-break', node()],
    ['home-task-own', node()],
    ['home-task-break-form', node()],
    ['home-task-steps', node()],
    ['home-task-break-save', node()],
    ['home-task-step-title', node({ value: '' })],
    ['home-task-step-add', node()],
    ['home-task-status', node()],
    ['home-task-off', node()],
    ['home-tasks', node({ hidden: false })],
    ['home-checkin', node()],
    ['home-checkin-answer', node()],
    ['home-checkin-on', node()],
    ['home-checkin-off', node()],
    ['home-checkin-status', node()],
  ]);
  if (chat) {
    for (const id of ['talk-log', 'talk-form', 'talk-input', 'talk-send', 'talk-status', 'talk-suggestions']) nodes.set(id, node());
  }
  const requests = [];
  const navigation = [];
  const context = vm.createContext({
    document: {
      getElementById(id) { return nodes.get(id); },
      querySelectorAll() { return []; },
      createElement() { return node(); },
    },
    window: { dispatchEvent() {}, requestAnimationFrame() {}, setInterval() {}, mhmRandom: random },
    Event,
    location: { replace(url) { navigation.push(url); }, assign(url) { navigation.push(url); } },
    fetch: fetchImpl || (async (url, options = {}) => {
      requests.push({ url, options });
      if (url === '/api/account') return Response.json(account);
      if (url === '/api/tasks?status=active') return Response.json(tasks);
      if (url === '/api/tasks/effort') return Response.json(efforts);
      if (url === '/api/checkins') return Response.json({ active: false, enabled: true, energy_today: energy });
      if (url === '/api/actions') return Response.json({ ok: true, message: 'Your check-in was queued for delivery.' });
      if (String(url).endsWith('/breakdown')) return Response.json({ steps: ['Ask if the refill is ready'] });
      if (String(url).endsWith('/subtasks')) return Response.json({ message: 'Added 1 smaller step. The original task stays.' });
      return Response.json({ error: 'missing' }, { status: 404 });
    }),
    Response,
  });
  vm.runInContext(source, context);
  for (let i = 0; i < 8; i += 1) await new Promise(resolve => setImmediate(resolve));
  return { nodes, requests, navigation, async checkin() {
    await nodes.get('home-checkin').listeners.click({ currentTarget: nodes.get('home-checkin') });
  } };
}

test('new accounts are sent through first-run setup before home loads', async () => {
  const view = await page({ account: { preferred_name: 'Brook', needs_setup: true, messages_enabled: false, tasks_enabled: false, checkins_enabled: false } });
  assert.deepEqual(view.navigation, ['setup.html']);
  assert.equal(view.nodes.get('home-content').hidden, true);
});

test('accounts with every support feature off stay on home', async () => {
  const view = await page({
    account: { preferred_name: 'Brook', messages_enabled: false, tasks_enabled: false, checkins_enabled: false },
  });
  assert.deepEqual(view.navigation, []);
  assert.equal(view.nodes.get('home-content').hidden, false);
});

test('home stays put when the account summary omits setup flags', async () => {
  const view = await page({
    account: { preferred_name: 'Brook' },
    fetchImpl: async (url) => {
      if (url === '/api/account') return Response.json({ preferred_name: 'Brook' });
      if (url === '/api/tasks?status=active') return Response.json({ tasks: [] });
      if (url === '/api/tasks/effort') return Response.json({ tasks: [] });
      return Response.json({ tasks: [] });
    },
  });
  assert.deepEqual(view.navigation, []);
  assert.equal(view.nodes.get('home-content').hidden, false);
});

test('home suggests the overdue task and explains why', async () => {
  const view = await page();
  assert.equal(view.nodes.get('home-name').textContent, 'River');
  assert.equal(view.nodes.get('home-task-title').textContent, 'Drink water');
  assert.match(view.nodes.get('home-task-meta').textContent, /Overdue/);
  assert.match(view.nodes.get('home-task-why').textContent, /overdue/i);
  assert.equal(view.nodes.get('home-task-actions').hidden, false);
  assert.equal(view.nodes.get('home-task-off').hidden, true);
  assert.equal(view.nodes.get('home-content').hidden, false);
});

test('home prefers a due-today task over a later one and skips a snoozed task', async () => {
  const later = new Date(Date.now() + 2 * 60 * 60 * 1000);
  const pad = value => String(value).padStart(2, '0');
  const snoozedUntil = `${later.getFullYear()}-${pad(later.getMonth() + 1)}-${pad(later.getDate())} ${pad(later.getHours())}:${pad(later.getMinutes())}:00`;
  const today = new Date();
  const todayKey = `${today.getFullYear()}-${pad(today.getMonth() + 1)}-${pad(today.getDate())}`;
  const view = await page({
    tasks: {
      tasks: [
        { id: 'later', title: 'File taxes', due_date: '2099-01-01', priority: 'critical' },
        { id: 'snoozed', title: 'Call pharmacy', due_date: todayKey, priority: 'high', reminder_snooze_until: snoozedUntil },
        { id: 'today', title: 'Water plants', due_date: todayKey, priority: 'low' },
      ],
    },
  });
  assert.equal(view.nodes.get('home-task-title').textContent, 'Water plants');
  assert.match(view.nodes.get('home-task-meta').textContent, /Due today/);
  assert.match(view.nodes.get('home-task-why').textContent, /This is due today/);
});

test('a short due-today task is preferred, and a low roll can still pick another fit', async () => {
  const today = new Date();
  const pad = value => String(value).padStart(2, '0');
  const todayKey = `${today.getFullYear()}-${pad(today.getMonth() + 1)}-${pad(today.getDate())}`;
  const tasks = {
    tasks: [
      { id: 'long', title: 'Clean the whole house', due_date: todayKey, priority: 'medium' },
      { id: 'short', title: 'Call pharmacy', due_date: todayKey, priority: 'medium' },
    ],
  };
  const efforts = { tasks: [{ id: 'long', minutes: 120 }, { id: 'short', minutes: 5 }] };
  const usual = await page({ tasks, efforts });
  assert.equal(usual.nodes.get('home-task-title').textContent, 'Call pharmacy');
  assert.match(usual.nodes.get('home-task-meta').textContent, /About 5 minutes/);
  assert.match(usual.nodes.get('home-task-why').textContent, /easiest useful/);
  const surprise = await page({ tasks, efforts, random: () => 0.99 });
  assert.equal(surprise.nodes.get('home-task-title').textContent, 'Clean the whole house');
});

test('done, later, and break it down call the task actions', async () => {
  const today = new Date();
  const pad = value => String(value).padStart(2, '0');
  const todayKey = `${today.getFullYear()}-${pad(today.getMonth() + 1)}-${pad(today.getDate())}`;
  const view = await page({
    tasks: { tasks: [{ id: 'pharmacy', title: 'Call pharmacy', due_date: todayKey, priority: 'medium' }] },
  });
  await view.nodes.get('home-task-done').listeners.click();
  const done = view.requests.find(request => request.url === '/api/tasks/pharmacy/complete');
  assert.equal(JSON.parse(done.options.body).completion_date, todayKey);
  await view.nodes.get('home-task-later').listeners.click();
  const later = view.requests.find(request => request.url === '/api/tasks/pharmacy/snooze');
  assert.deepEqual(JSON.parse(later.options.body), { option: '1_hour' });
  await view.nodes.get('home-task-break').listeners.click();
  assert.equal(view.nodes.get('home-task-break-form').hidden, false);
  const breakdown = view.requests.find(request => request.url === '/api/tasks/pharmacy/breakdown');
  assert.deepEqual(JSON.parse(breakdown.options.body), {});
  await view.nodes.get('home-task-break-save').listeners.click();
  const added = view.requests.find(request => request.url === '/api/tasks/pharmacy/subtasks');
  assert.deepEqual(JSON.parse(added.options.body), { titles: ['Ask if the refill is ready'] });
});

test('home picks an open subtask and keeps the bigger task', async () => {
  const today = new Date();
  const pad = value => String(value).padStart(2, '0');
  const todayKey = `${today.getFullYear()}-${pad(today.getMonth() + 1)}-${pad(today.getDate())}`;
  const view = await page({
    tasks: {
      tasks: [
        { id: 'dentist', title: 'Call the dentist', due_date: todayKey, priority: 'high' },
        { id: 'phone', title: 'Find the phone number', due_date: todayKey, priority: 'low', parent_id: 'dentist' },
      ],
    },
  });
  assert.equal(view.nodes.get('home-task-title').textContent, 'Find the phone number');
  assert.match(view.nodes.get('home-task-why').textContent, /Part of Call the dentist/);
  assert.equal(view.nodes.get('home-task-break').hidden, true);
  assert.equal(view.nodes.get('home-task-own').hidden, false);
  await view.nodes.get('home-task-own').listeners.click();
  const detached = view.requests.find(request => request.url === '/api/tasks/phone/detach');
  assert.deepEqual(JSON.parse(detached.options.body), {});
});

test('home can add a step you type', async () => {
  const today = new Date();
  const pad = value => String(value).padStart(2, '0');
  const todayKey = `${today.getFullYear()}-${pad(today.getMonth() + 1)}-${pad(today.getDate())}`;
  const view = await page({
    tasks: { tasks: [{ id: 'kitchen', title: 'Clean the kitchen', due_date: todayKey, priority: 'medium' }] },
  });
  view.nodes.get('home-task-step-title').value = 'Wipe the counter';
  await view.nodes.get('home-task-step-add').listeners.click();
  const added = view.requests.find(request => request.url === '/api/tasks/kitchen/subtasks');
  assert.deepEqual(JSON.parse(added.options.body), { titles: ['Wipe the counter'] });
});

test('home returns to the bigger task when its smaller step is set aside', async () => {
  const later = new Date(Date.now() + 2 * 60 * 60 * 1000);
  const pad = value => String(value).padStart(2, '0');
  const snoozedUntil = `${later.getFullYear()}-${pad(later.getMonth() + 1)}-${pad(later.getDate())} ${pad(later.getHours())}:${pad(later.getMinutes())}:00`;
  const today = new Date();
  const todayKey = `${today.getFullYear()}-${pad(today.getMonth() + 1)}-${pad(today.getDate())}`;
  const view = await page({
    tasks: {
      tasks: [
        { id: 'dentist', title: 'Call the dentist', due_date: todayKey, priority: 'high' },
        { id: 'phone', title: 'Find the phone number', due_date: todayKey, priority: 'low', parent_id: 'dentist', reminder_snooze_until: snoozedUntil },
      ],
    },
  });
  assert.equal(view.nodes.get('home-task-title').textContent, 'Call the dentist');
  assert.equal(view.nodes.get('home-task-break').hidden, false);
});

test('home points back to an open check-in', async () => {
  const view = await page({
    fetchImpl: async (url) => {
      if (url === '/api/account') return Response.json({ preferred_name: 'River', needs_setup: false, tasks_enabled: true, checkins_enabled: true });
      if (url === '/api/tasks?status=active') return Response.json({ tasks: [] });
      if (url === '/api/checkins') return Response.json({ active: true, index: 2, total: 3, question_type: 'yes_no' });
      return Response.json({ error: 'missing' }, { status: 404 });
    },
  });
  assert.match(view.nodes.get('home-checkin-on').textContent, /Question 2 of 3/);
  assert.equal(view.nodes.get('home-checkin-answer').textContent, 'Continue check-in');
  assert.equal(view.nodes.get('home-checkin-answer').hidden, false);
});

test('home warns when task reminders are off', async () => {
  const view = await page({
    account: { preferred_name: 'River', needs_setup: false, tasks_enabled: false, checkins_enabled: true },
  });
  assert.equal(view.nodes.get('home-task-off').hidden, false);
  assert.equal(view.nodes.get('home-tasks').hidden, false);
  assert.equal(view.nodes.get('home-task-title').textContent, 'Drink water');
  assert.equal(view.requests.some(request => request.url === '/api/tasks?status=active'), true);
  assert.equal(view.nodes.get('home-checkin-off').hidden, true);
});

test('a scheduled message in the chat can ask for more like it', async () => {
  const reactions = [];
  const view = await page({
    chat: true,
    fetchImpl: async (url, options = {}) => {
      if (url === '/api/account') return Response.json({ preferred_name: 'River', needs_setup: false, tasks_enabled: true, checkins_enabled: true });
      if (url === '/api/tasks?status=active') return Response.json({ tasks: [] });
      if (url === '/api/tasks/effort') return Response.json({ tasks: [] });
      if (url === '/api/checkins') return Response.json({ active: false, enabled: true });
      if (url === '/api/chat/reactions') {
        reactions.push(JSON.parse(options.body));
        return Response.json({ status: 'liked', reply: "I'll send more messages like that." });
      }
      if (url === '/api/chat') {
        const recent = new Date().toISOString();
        return Response.json({
          turns: [
            { role: 'you', text: 'hi', created_at: recent },
            { role: 'mhm', text: 'Hello from the website.', created_at: recent },
            { role: 'mhm', text: 'Keep going.', created_at: recent, delivery_id: 'delivery-1', reaction: '' },
          ],
        });
      }
      return Response.json({ error: 'missing' }, { status: 404 });
    },
  });
  const bubbles = view.nodes.get('talk-log').childNodes.filter(item => String(item.className || '').includes('talk-bubble'));
  const reactable = bubbles.filter(item => item.childNodes.some(child => child.className === 'talk-reactions'));
  assert.equal(reactable.length, 1);
  assert.match(reactable[0].childNodes.find(child => child.tagName === 'P' || child.textContent === 'Keep going.').textContent, /Keep going/);
  const choices = reactable[0].childNodes.find(child => child.className === 'talk-reactions');
  const more = choices.childNodes.find(child => child.textContent === 'More like this');
  assert.equal(more.getAttribute('aria-pressed'), 'false');
  await more.listeners.click();
  assert.deepEqual(reactions, [{ delivery_id: 'delivery-1', kind: 'up' }]);
  assert.equal(more.getAttribute('aria-pressed'), 'true');
  assert.equal(view.nodes.get('talk-status').textContent, "I'll send more messages like that.");
});

test('a long task due today is not called the easiest one', async () => {
  const today = new Date();
  const pad = value => String(value).padStart(2, '0');
  const todayKey = `${today.getFullYear()}-${pad(today.getMonth() + 1)}-${pad(today.getDate())}`;
  const view = await page({
    tasks: { tasks: [{ id: 'house', title: 'Clean the whole house', due_date: todayKey, priority: 'medium' }] },
    efforts: { tasks: [{ id: 'house', minutes: 120 }] },
  });
  assert.equal(view.nodes.get('home-task-title').textContent, 'Clean the whole house');
  assert.match(view.nodes.get('home-task-why').textContent, /will take a while/);
  assert.doesNotMatch(view.nodes.get('home-task-why').textContent, /easiest/);
});

test('low energy prefers a short task over a longer one', async () => {
  const view = await page({
    energy: 2,
    tasks: {
      tasks: [
        { id: 'long', title: 'Rewrite the notes', priority: 'high' },
        { id: 'short', title: 'Send one email', priority: 'low' },
      ],
    },
    efforts: { tasks: [{ id: 'long', minutes: 25 }, { id: 'short', minutes: 10 }] },
  });
  assert.equal(view.nodes.get('home-task-title').textContent, 'Send one email');
  assert.match(view.nodes.get('home-task-why').textContent, /energy is low/);
});

test('home.js can load after app.js without a global status clash', async () => {
  const app = await readFile(new URL('./app.js', import.meta.url), 'utf8');
  const home = await readFile(new URL('./home.js', import.meta.url), 'utf8');
  const nodes = new Map([['app-status', node({ hidden: false })], ['home-content', node()], ['logout', node()]]);
  const context = vm.createContext({
    document: {
      getElementById(id) { return nodes.get(id) || node(); },
      querySelectorAll() { return []; },
      createElement() { return node(); },
    },
    window: { addEventListener() {}, dispatchEvent() { return true; }, setInterval() {}, requestAnimationFrame() {} },
    Event,
    URLSearchParams,
    AbortSignal: { timeout() { return undefined; } },
    location: { search: '', replace() {}, assign() {} },
    fetch: async (url) => Response.json(url === '/api/account' ? { preferred_name: 'River', needs_setup: false, tasks_enabled: false, checkins_enabled: false } : { tasks: [] }),
    Response,
  });
  vm.runInContext(app, context);
  vm.runInContext(home, context);
});

test('failed chat sends restore the message for a quick retry', async () => {
  const view = await page({
    chat: true,
    fetchImpl: async (url, options = {}) => {
      if (url === '/api/account') return Response.json({ preferred_name: 'River', needs_setup: false, tasks_enabled: true, checkins_enabled: true });
      if (url === '/api/tasks?status=active') return Response.json({ tasks: [] });
      if (url === '/api/tasks/effort') return Response.json({ tasks: [] });
      if (url === '/api/checkins') return Response.json({ active: false, enabled: true });
      if (url === '/api/chat' && options.method === 'POST') throw new Error('Connection dropped.');
      if (url === '/api/chat') return Response.json({ turns: [] });
      return Response.json({ error: 'missing' }, { status: 404 });
    },
  });
  const input = view.nodes.get('talk-input');
  const send = view.nodes.get('talk-send');
  input.value = 'Please help me plan today';
  await view.nodes.get('talk-form').listeners.submit({ preventDefault() {} });
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(input.value, 'Please help me plan today');
  assert.equal(send.disabled, false);
  assert.equal(send.getAttribute('aria-busy'), undefined);
  assert.equal(view.nodes.get('talk-status').textContent, 'Connection dropped.');
  const failedCopies = view.nodes.get('talk-log').childNodes
    .flatMap(item => item.childNodes || [])
    .filter(item => item.textContent === 'Please help me plan today');
  assert.equal(failedCopies.length, 0);
});

test('chat enter shortcut does not submit while text composition is active', () => {
  assert.match(source, /!event\.isComposing/);
});

test('home task actions share one busy lock', () => {
  assert.match(source, /function setFocusBusy\(busy\)/);
  assert.match(source, /if \(!focusedTask \|\| focusActionBusy\) return/);
  assert.match(source, /actions\.setAttribute\('aria-busy', 'true'\)/);
  assert.match(source, /const taskId = focusedTask\.id/);
});
