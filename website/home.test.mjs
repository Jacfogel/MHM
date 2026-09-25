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
    addEventListener(type, listener) { this.listeners = this.listeners || {}; this.listeners[type] = listener; },
    append(...children) { this.childNodes.push(...children); },
    replaceChildren(...children) { this.childNodes = children; },
    focus() {},
    ...extras,
  };
}

async function page({ account = { preferred_name: 'River', needs_setup: false, tasks_enabled: true, checkins_enabled: true }, tasks = { tasks: [{ title: 'Drink water', due_date: '2026-09-21', due_time: '09:00' }] }, efforts = { tasks: [] }, fetchImpl, random = () => 0 } = {}) {
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
    ['home-task-break-form', node()],
    ['home-task-smaller', node({ value: '' })],
    ['home-task-break-save', node()],
    ['home-task-status', node()],
    ['home-task-off', node()],
    ['home-tasks', node({ hidden: false })],
    ['home-checkin', node()],
    ['home-checkin-answer', node()],
    ['home-checkin-on', node()],
    ['home-checkin-off', node()],
    ['home-checkin-status', node()],
    ['home-capture-form', node()],
    ['home-note', node({ value: 'A parked thought' })],
    ['home-capture-submit', node()],
    ['home-capture-status', node()],
    ['home-recent-notes', node()],
  ]);
  const requests = [];
  const navigation = [];
  const context = vm.createContext({
    document: {
      getElementById(id) { return nodes.get(id); },
      querySelectorAll() { return []; },
      createElement() { return node(); },
    },
    window: { dispatchEvent() {}, requestAnimationFrame() {}, mhmRandom: random },
    Event,
    location: { replace(url) { navigation.push(url); }, assign(url) { navigation.push(url); } },
    fetch: fetchImpl || (async (url, options = {}) => {
      requests.push({ url, options });
      if (url === '/api/account') return Response.json(account);
      if (url === '/api/tasks?status=active') return Response.json(tasks);
      if (url === '/api/tasks/effort') return Response.json(efforts);
      if (url === '/api/checkins') return Response.json({ active: false, enabled: true });
      if (url === '/api/notes?status=active') return Response.json({ notes: [] });
      if (url === '/api/notes') return Response.json({ ok: true }, { status: 201 });
      if (url === '/api/actions') return Response.json({ ok: true, message: 'Your check-in was queued for delivery.' });
      return Response.json({ error: 'missing' }, { status: 404 });
    }),
    Response,
  });
  vm.runInContext(source, context);
  for (let i = 0; i < 8; i += 1) await new Promise(resolve => setImmediate(resolve));
  return { nodes, requests, navigation, async capture() {
    await nodes.get('home-capture-form').listeners.submit({ preventDefault() {} });
  }, async checkin() {
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
      if (url === '/api/notes?status=active') return Response.json({ notes: [] });
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
  assert.match(view.nodes.get('home-task-why').textContent, /easiest useful/);
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
  view.nodes.get('home-task-smaller').value = 'Ask if the refill is ready';
  await view.nodes.get('home-task-break-form').listeners.submit({ preventDefault() {} });
  const smaller = view.requests.find(request => request.url === '/api/tasks/pharmacy/simplify');
  assert.deepEqual(JSON.parse(smaller.options.body), { new_title: 'Ask if the refill is ready' });
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

test('a one-line capture is saved as a notebook note', async () => {
  const view = await page();
  await view.capture();
  const saved = view.requests.find(request => request.url === '/api/notes');
  assert.deepEqual(JSON.parse(saved.options.body), {
    kind: 'note',
    title: 'A parked thought',
    description: 'A parked thought',
  });
  assert.equal(view.nodes.get('home-note').value, '');
});

test('home lists recent note titles under the capture box', async () => {
  const view = await page({
    fetchImpl: async (url) => {
      if (url === '/api/account') return Response.json({ preferred_name: 'River', needs_setup: false, tasks_enabled: true, checkins_enabled: true });
      if (url === '/api/tasks?status=active') return Response.json({ tasks: [] });
      if (url === '/api/tasks/effort') return Response.json({ tasks: [] });
      if (url === '/api/checkins') return Response.json({ active: false, enabled: true });
      if (url === '/api/notes?status=active') {
        return Response.json({
          notes: [
            { title: 'Pharmacy call' },
            { title: '', description: 'The gate code is on the fridge' },
          ],
        });
      }
      return Response.json({ error: 'missing' }, { status: 404 });
    },
  });
  const labels = view.nodes.get('home-recent-notes').childNodes.map(item => item.childNodes[0].textContent);
  assert.deepEqual(labels, ['Pharmacy call', 'The gate code is on the fridge']);
  assert.equal(view.nodes.get('home-recent-notes').childNodes[0].childNodes[0].href, 'notes.html');
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
