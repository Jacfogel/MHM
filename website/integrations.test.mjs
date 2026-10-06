import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import vm from 'node:vm';

const source = await readFile(new URL('./integrations.js', import.meta.url), 'utf8');

function element() {
  const classes = new Set();
  return {
    hidden: false,
    disabled: false,
    textContent: '',
    attributes: {},
    listeners: {},
    classList: {
      add(name) { classes.add(name); },
      remove(name) { classes.delete(name); },
      contains(name) { return classes.has(name); },
    },
    setAttribute(name, value) { this.attributes[name] = value; },
    removeAttribute(name) { delete this.attributes[name]; },
    addEventListener(type, listener) { this.listeners[type] = listener; },
  };
}

async function settle() {
  await new Promise(resolve => setImmediate(resolve));
  await new Promise(resolve => setImmediate(resolve));
}

async function page(fetchImpl, { open = () => ({ opener: 'parent' }), confirm = () => true } = {}) {
  const ids = [
    'health-status-message', 'health-card', 'health-connect', 'health-enable', 'health-pause',
    'health-sync', 'health-delete', 'health-feature-state', 'health-connected', 'health-last-sync',
    'health-guidance',
  ];
  const nodes = new Map(ids.map(id => [id, element()]));
  const requests = [];
  const assigned = [];
  const replaced = [];
  const window = new EventTarget();
  window.open = open;
  window.confirm = confirm;
  vm.runInContext(source, vm.createContext({
    document: { getElementById(id) { return nodes.get(id); } },
    window,
    Event,
    location: {
      assign(url) { assigned.push(url); },
      replace(url) { replaced.push(url); },
    },
    fetch: async (path, options) => {
      const request = {
        path,
        method: options.method,
        body: options.body ? JSON.parse(options.body) : undefined,
      };
      requests.push(request);
      return fetchImpl(request);
    },
  }));
  await settle();
  return { nodes, requests, assigned, replaced };
}

const connectedHealth = {
  feature_state: 'enabled',
  connected: true,
  connect_available: true,
  connecting: false,
  last_success_at: '2026-10-05 09:00',
};

test('health status renders connection state and useful setup guidance', async () => {
  const screen = await page(async () => Response.json({
    feature_state: 'disabled',
    connected: false,
    connect_available: false,
    connecting: false,
    connect_error: 'Google Health needs configuration.',
    last_success_at: null,
  }));

  assert.equal(screen.nodes.get('health-card').hidden, false);
  assert.equal(screen.nodes.get('health-feature-state').textContent, 'disabled');
  assert.equal(screen.nodes.get('health-connected').textContent, 'No');
  assert.equal(screen.nodes.get('health-last-sync').textContent, 'Never');
  assert.equal(screen.nodes.get('health-connect').disabled, true);
  assert.equal(screen.nodes.get('health-guidance').textContent, 'Google Health needs configuration.');
});

test('health sync is single-flight and restores every control after saving', async () => {
  let finishSaving;
  const screen = await page(async request => {
    if (request.method === 'GET') return Response.json(connectedHealth);
    return new Promise(resolve => { finishSaving = resolve; });
  });
  const sync = screen.nodes.get('health-sync').listeners.click;

  const saving = sync();
  sync();

  assert.equal(screen.requests.filter(request => request.method === 'POST').length, 1);
  assert.deepEqual(screen.requests.at(-1).body, { action: 'sync' });
  assert.equal(screen.nodes.get('health-card').attributes['aria-busy'], 'true');
  for (const action of ['connect', 'enable', 'pause', 'sync', 'delete']) {
    assert.equal(screen.nodes.get(`health-${action}`).disabled, true);
  }

  finishSaving(Response.json({ ...connectedHealth, message: 'Health data synced.' }));
  await saving;

  assert.equal(screen.nodes.get('health-card').attributes['aria-busy'], undefined);
  assert.equal(screen.nodes.get('health-status-message').textContent, 'Health data synced.');
  assert.equal(screen.nodes.get('health-sync').disabled, false);
});

test('a blocked health connection popup continues in the current tab', async () => {
  const screen = await page(async request => (
    request.method === 'GET'
      ? Response.json({ ...connectedHealth, connected: false })
      : Response.json({ ...connectedHealth, connected: false, url: 'https://health.example/connect' })
  ), { open: () => null });

  await screen.nodes.get('health-connect').listeners.click();

  assert.deepEqual(screen.assigned, ['https://health.example/connect']);
});

test('health actions disable every integration control while saving', () => {
  assert.match(source, /if \(healthBusy\) return/);
  assert.match(source, /for \(const button of healthButtons\) button\.disabled = busy/);
  assert.match(source, /healthCard\.setAttribute\('aria-busy', 'true'\)/);
  assert.match(source, /healthCard\.removeAttribute\('aria-busy'\)/);
});

test('blocked health connection popups fall back to the current tab', () => {
  assert.match(source, /const opened = window\.open\(result\.url, '_blank'\)/);
  assert.match(source, /if \(opened\) opened\.opener = null/);
  assert.match(source, /else location\.assign\(result\.url\)/);
});
