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
    addEventListener(type, listener) { this.listeners = this.listeners || {}; this.listeners[type] = listener; },
    ...extras,
  };
}

async function page({ account = { preferred_name: 'River', needs_setup: false, tasks_enabled: true, checkins_enabled: true }, tasks = { tasks: [{ title: 'Drink water', due_date: '2026-09-21', due_time: '09:00' }] }, fetchImpl } = {}) {
  const nodes = new Map([
    ['app-status', node({ hidden: false })],
    ['home-content', node()],
    ['home-name', node()],
    ['home-task-title', node()],
    ['home-task-meta', node()],
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
  ]);
  const requests = [];
  const navigation = [];
  const context = vm.createContext({
    document: {
      getElementById(id) { return nodes.get(id); },
    },
    window: { dispatchEvent() {} },
    Event,
    location: { replace(url) { navigation.push(url); }, assign(url) { navigation.push(url); } },
    fetch: fetchImpl || (async (url, options = {}) => {
      requests.push({ url, options });
      if (url === '/api/account') return Response.json(account);
      if (url === '/api/tasks?status=active') return Response.json(tasks);
      if (url === '/api/checkins') return Response.json({ active: false, enabled: true });
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

test('accounts with every support feature off are sent through setup even without needs_setup', async () => {
  const view = await page({
    account: { preferred_name: 'Brook', messages_enabled: false, tasks_enabled: false, checkins_enabled: false },
  });
  assert.deepEqual(view.navigation, ['setup.html']);
});

test('home uses saved settings when the account summary omits setup flags', async () => {
  const view = await page({
    account: { preferred_name: 'Brook' },
    fetchImpl: async (url) => {
      if (url === '/api/account') return Response.json({ preferred_name: 'Brook' });
      if (url === '/api/settings') {
        return Response.json({
          sections: {
            messages: { enabled: false },
            tasks: { enabled: false },
            checkins: { enabled: false },
          },
        });
      }
      return Response.json({ tasks: [] });
    },
  });
  assert.deepEqual(view.navigation, ['setup.html']);
});

test('home shows the next due task and can queue a check-in', async () => {
  const view = await page();
  assert.equal(view.nodes.get('home-name').textContent, 'River');
  assert.equal(view.nodes.get('home-task-title').textContent, 'Drink water');
  assert.match(view.nodes.get('home-task-meta').textContent, /2026-09-21/);
  assert.equal(view.nodes.get('home-task-off').hidden, true);
  assert.equal(view.nodes.get('home-checkin').hidden, false);
  assert.equal(view.nodes.get('home-content').hidden, false);
  await view.checkin();
  assert.ok(view.requests.some(request => request.url === '/api/actions' && JSON.parse(request.options.body).action === 'checkin_prompt'));
  assert.match(view.nodes.get('home-checkin-status').textContent, /queued/);
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

test('home.js can load after app.js without a global status clash', async () => {
  const app = await readFile(new URL('./app.js', import.meta.url), 'utf8');
  const home = await readFile(new URL('./home.js', import.meta.url), 'utf8');
  const nodes = new Map([['app-status', node({ hidden: false })], ['home-content', node()], ['logout', node()]]);
  const context = vm.createContext({
    document: { getElementById(id) { return nodes.get(id) || node(); } },
    window: { addEventListener() {}, dispatchEvent() { return true; } },
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
