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
    children: [],
    classList: { add() {}, remove() {}, toggle() {} },
    setAttribute() {},
    removeAttribute() {},
    replaceChildren(...children) { this.children = children; },
    append(child) { this.children.push(child); },
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

async function page() {
  const nodes = new Map([
    ['setup-status', node()],
    ['setup-content', node()],
    ['setup-continue', node({ textContent: 'Continue →' })],
    ['setup-skip', node()],
    ['step-1', node({ hidden: false })],
    ['step-2', node()],
    ['step-3', node()],
    ['progress-1', node()],
    ['progress-2', node()],
    ['progress-3', node()],
    ['preferred-name', node({ value: '' })],
    ['timezone', node({ value: '' })],
    ['enable-messages', node({ checked: true })],
    ['enable-tasks', node({ checked: true })],
    ['enable-checkins', node({ checked: true })],
    ['first-task', node({ value: 'Drink water' })],
    ['setup-form', node()],
  ]);
  const requests = [];
  const navigation = [];
  let current = snapshot();
  const context = vm.createContext({
    document: {
      getElementById(id) { return nodes.get(id); },
      createElement() { return node(); },
    },
    window: { dispatchEvent() {} },
    Event,
    Intl: { DateTimeFormat() { return { resolvedOptions() { return { timeZone: 'America/Regina' }; } }; } },
    location: { replace(url) { navigation.push(url); }, assign(url) { navigation.push(url); } },
    fetch: async (url, options = {}) => {
      requests.push({ url, method: options.method || 'GET', body: options.body });
      if (url === '/api/account') return Response.json({ preferred_name: 'Brook', timezone: 'America/Regina', needs_setup: true });
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
      return Response.json({ error: 'missing' }, { status: 404 });
    },
    Response,
  });
  vm.runInContext(source, context);
  for (let i = 0; i < 8; i += 1) await new Promise(resolve => setImmediate(resolve));
  return { nodes, requests, navigation, async continue() {
    await nodes.get('setup-form').listeners.submit({ preventDefault() {} });
    await new Promise(resolve => setImmediate(resolve));
  } };
}

test('first-run walks name, support choices, and a first task', async () => {
  const view = await page();
  assert.equal(view.nodes.get('setup-content').hidden, false);
  assert.equal(view.nodes.get('preferred-name').value, 'Brook');
  view.nodes.get('preferred-name').value = 'River';
  await view.continue();
  assert.equal(view.nodes.get('step-2').hidden, false);
  await view.continue();
  assert.equal(view.nodes.get('step-3').hidden, false);
  await view.continue();
  const settingsPosts = view.requests.filter(request => request.url === '/api/settings' && request.method === 'POST').map(request => JSON.parse(request.body));
  assert.equal(settingsPosts[0].section, 'profile');
  assert.equal(settingsPosts[0].values.preferred_name, 'River');
  assert.equal(settingsPosts[1].section, 'delivery');
  assert.equal(settingsPosts[2].section, 'messages');
  assert.equal(settingsPosts[2].values.enabled, true);
  assert.deepEqual(settingsPosts[2].values.categories, ['motivational']);
  assert.equal(settingsPosts[3].section, 'tasks');
  assert.equal(settingsPosts[3].values.enabled, true);
  assert.equal(settingsPosts[4].section, 'checkins');
  assert.equal(settingsPosts[4].values.enabled, true);
  const task = view.requests.find(request => request.url === '/api/tasks');
  assert.deepEqual(JSON.parse(task.body), { title: 'Drink water' });
  assert.deepEqual(view.navigation, ['home.html']);
});
