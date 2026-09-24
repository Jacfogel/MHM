import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';

const source = await readFile(new URL('./setup.js', import.meta.url), 'utf8');

function node(extras = {}) {
  return {
    hidden: true,
    disabled: false,
    textContent: '',
    value: '',
    checked: false,
    selected: false,
    required: false,
    dataset: {},
    children: [],
    classList: { add() {}, remove() {}, toggle() {} },
    setAttribute(name, value) { this[name] = value; },
    removeAttribute(name) { delete this[name]; },
    replaceChildren(...children) { this.children = children; },
    append(...children) { this.children.push(...children); },
    querySelectorAll() { return []; },
    addEventListener(type, listener) { this.listeners = this.listeners || {}; this.listeners[type] = listener; },
    ...extras,
  };
}

function snapshot() {
  return {
    sections: {
      profile: { preferred_name: 'Brook', date_of_birth: '', pronouns: [] },
      delivery: { timezone: 'America/Regina', channel: 'email' },
      messages: { enabled: false, categories: [], periods: {} },
      tasks: { enabled: false, periods: {}, recurring: { default_recurrence_pattern: null, default_recurrence_interval: 1, default_repeat_after_completion: true } },
      checkins: { enabled: false, periods: {}, questions: { mood: 'sometimes' }, custom_questions: {}, min_questions: 2, max_questions: 3 },
    },
    revisions: { profile: 'p1', delivery: 'd1', messages: 'm1', tasks: 't1', checkins: 'c1' },
    options: { timezones: ['America/Regina', 'UTC'], categories: ['motivational'] },
    available_message_periods: { motivational: {} },
  };
}

async function page({ account = { preferred_name: 'Brook', timezone: 'America/Regina', needs_setup: true } } = {}) {
  const nodes = new Map([
    ['setup-status', node()],
    ['setup-content', node()],
    ['setup-continue', node({ textContent: 'Continue →' })],
    ['setup-skip', node()],
    ['setup-back', node()],
    ['setup-progress', node()],
    ['step-1', node({ hidden: false })],
    ['step-discord', node()],
    ['step-2', node()],
    ['step-message-categories', node()],
    ['step-message-windows', node()],
    ['step-task-create', node()],
    ['step-task-windows', node()],
    ['step-checkin-questions', node()],
    ['step-checkin-windows', node()],
    ['preferred-name', node({ value: '' })],
    ['timezone', node({ value: '' })],
    ['enable-messages', node({ checked: false })],
    ['enable-tasks', node({ checked: true })],
    ['enable-checkins', node({ checked: false })],
    ['first-task', node({ value: 'Drink water' })],
    ['setup-connect-discord', node()],
    ['discord-setup-state', node()],
    ['message-categories', node()],
    ['message-windows', node()],
    ['task-windows', node()],
    ['checkin-questions', node()],
    ['checkin-windows', node()],
    ['setup-form', node()],
  ]);
  const requests = [];
  const navigation = [];
  let current = snapshot();
  const context = vm.createContext({
    document: {
      getElementById(id) { return nodes.get(id); },
      createElement() { return node(); },
      querySelectorAll() { return []; },
    },
    window: { dispatchEvent() {} },
    Event,
    URLSearchParams,
    crypto: { randomUUID() { return String(Math.random()); } },
    history: { replaceState() {} },
    Intl: { DateTimeFormat() { return { resolvedOptions() { return { timeZone: 'America/Regina' }; } }; } },
    location: { search: '', pathname: '/setup.html', replace(url) { navigation.push(url); }, assign(url) { navigation.push(url); } },
    fetch: async (url, options = {}) => {
      requests.push({ url, method: options.method || 'GET', body: options.body });
      if (url === '/api/account') return Response.json(account);
      if (url === '/api/settings' && options.method !== 'POST') return Response.json(current);
      if (url === '/api/settings') {
        const payload = JSON.parse(options.body);
        current = {
          ...current,
          sections: { ...current.sections, [payload.section]: payload.values },
          revisions: { ...current.revisions, [payload.section]: `${payload.section}-next` },
        };
        return Response.json(current);
      }
      if (url === '/api/tasks') return Response.json({ ok: true }, { status: 201 });
      if (url === '/api/account/setup-complete') return Response.json({ ok: true });
      return Response.json({ error: 'missing' }, { status: 404 });
    },
    Response,
  });
  vm.runInContext(source, context);
  for (let i = 0; i < 8; i += 1) await new Promise(resolve => setImmediate(resolve));
  return { nodes, requests, navigation, async continue() {
    await nodes.get('setup-form').listeners.submit({ preventDefault() {} });
    for (let i = 0; i < 4; i += 1) await new Promise(resolve => setImmediate(resolve));
  }, async skip() {
    await nodes.get('setup-skip').listeners.click();
    for (let i = 0; i < 4; i += 1) await new Promise(resolve => setImmediate(resolve));
  } };
}

test('first-run walks name, delivery, support choices, and a first task', async () => {
  const view = await page();
  assert.equal(view.nodes.get('setup-content').hidden, false);
  assert.equal(view.nodes.get('preferred-name').value, 'Brook');
  view.nodes.get('preferred-name').value = 'River';
  await view.continue();
  assert.equal(view.nodes.get('step-discord').hidden, false);
  await view.continue();
  assert.equal(view.nodes.get('step-2').hidden, false);
  view.nodes.get('enable-messages').checked = false;
  view.nodes.get('enable-checkins').checked = false;
  view.nodes.get('enable-tasks').checked = true;
  await view.continue();
  assert.equal(view.nodes.get('step-task-create').hidden, false);
  await view.continue();
  assert.equal(view.nodes.get('step-task-windows').hidden, false);
  await view.skip();
  const settingsPosts = view.requests.filter(request => request.url === '/api/settings' && request.method === 'POST').map(request => JSON.parse(request.body));
  assert.equal(settingsPosts.find(post => post.section === 'profile').values.preferred_name, 'River');
  assert.equal(settingsPosts.filter(post => post.section === 'delivery').length, 2);
  assert.equal(settingsPosts.find(post => post.section === 'messages').values.enabled, false);
  assert.equal(settingsPosts.find(post => post.section === 'tasks').values.enabled, true);
  assert.equal(settingsPosts.find(post => post.section === 'checkins').values.enabled, false);
  const task = view.requests.find(request => request.url === '/api/tasks');
  assert.deepEqual(JSON.parse(task.body), { title: 'Drink water' });
  assert.deepEqual(view.navigation, ['home.html']);
});

test('setup stays open when support features are all off even without needs_setup', async () => {
  const view = await page({
    account: { preferred_name: 'Brook', timezone: 'America/Regina' },
  });
  assert.deepEqual(view.navigation, []);
  assert.equal(view.nodes.get('setup-content').hidden, false);
});

test('accounts that already have a support feature skip setup', async () => {
  const view = await page({
    account: { preferred_name: 'River', timezone: 'America/Regina', needs_setup: false, messages_enabled: true, tasks_enabled: false, checkins_enabled: false },
  });
  assert.deepEqual(view.navigation, ['home.html']);
  assert.equal(view.nodes.get('setup-content').hidden, true);
});
