import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import vm from 'node:vm';

const source = await readFile(new URL('./messages.js', import.meta.url), 'utf8');
const html = await readFile(new URL('./messages.html', import.meta.url), 'utf8');

function element(tagName = 'div') {
  const classes = new Set();
  return {
    tagName: tagName.toUpperCase(),
    hidden: false,
    disabled: false,
    textContent: '',
    value: '',
    checked: false,
    className: '',
    childNodes: [],
    attributes: {},
    dataset: {},
    listeners: {},
    get children() { return this.childNodes; },
    get options() { return this.childNodes; },
    classList: {
      toggle(name, force) {
        if (force === undefined ? !classes.has(name) : force) classes.add(name);
        else classes.delete(name);
      },
      contains(name) { return classes.has(name); },
    },
    append(...children) { this.childNodes.push(...children); },
    replaceChildren(...children) { this.childNodes = children; },
    addEventListener(type, listener) { this.listeners[type] = listener; },
    setAttribute(name, value) { this.attributes[name] = value; },
    removeAttribute(name) { delete this.attributes[name]; },
    querySelectorAll(selector) {
      const matches = [];
      const visit = child => {
        if (child.tagName === 'INPUT' && (selector === 'input' || (selector === 'input:checked' && child.checked))) matches.push(child);
        for (const grandchild of child.childNodes || []) visit(grandchild);
      };
      for (const child of this.childNodes) visit(child);
      return matches;
    },
    focus() { this.focused = true; },
    reset() {},
  };
}

async function settle() {
  await new Promise(resolve => setImmediate(resolve));
  await new Promise(resolve => setImmediate(resolve));
}

function library({ category = 'motivation', messages = [] } = {}) {
  return {
    categories: ['motivation', 'rest', 'focus'],
    category,
    messages,
    period_names: ['Morning', 'Evening'],
  };
}

async function page(fetchImpl, { confirm = () => true } = {}) {
  const ids = [
    'message-category', 'messages-status', 'messages-workspace', 'message-form', 'message-text',
    'message-active', 'message-days', 'message-periods', 'message-list', 'messages-empty',
    'messages-summary', 'message-cancel', 'message-preview-text', 'message-preview-meta',
    'message-test', 'message-extra-fields', 'message-more-options', 'message-form-title',
  ];
  const nodes = new Map(ids.map(id => [id, element()]));
  nodes.get('messages-workspace').hidden = true;
  const submit = element('button');
  nodes.get('message-form').querySelector = selector => selector === 'button[type="submit"]' ? submit : null;
  const document = {
    getElementById(id) { return nodes.get(id); },
    createElement(tagName) { return element(tagName); },
    createTextNode(value) { const node = element('#text'); node.textContent = value; return node; },
  };
  const requests = [];
  const navigation = [];
  const window = new EventTarget();
  window.confirm = confirm;
  vm.runInContext(source, vm.createContext({
    document,
    window,
    Event,
    HTMLInputElement: class {},
    location: { replace(url) { navigation.push(url); } },
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
  return { nodes, requests, navigation, submit };
}

test('message library loads categories and renders personal messages', async () => {
  const screen = await page(async () => Response.json(library({
    messages: [{ id: 'one', text: 'One gentle step.', active: true, days: ['ALL'], periods: ['Morning'] }],
  })));

  assert.equal(screen.nodes.get('messages-workspace').hidden, false);
  assert.equal(screen.nodes.get('message-category').options.length, 3);
  assert.equal(screen.nodes.get('message-category').value, 'motivation');
  assert.equal(screen.nodes.get('messages-summary').textContent, '1 personal message');
  assert.equal(screen.nodes.get('message-list').childNodes.length, 1);
  assert.equal(screen.nodes.get('message-list').childNodes[0].childNodes[0].childNodes[0].textContent, 'One gentle step.');
});

test('new messages save their selected schedule and reload the category', async () => {
  const screen = await page(async request => {
    if (request.method === 'POST') return Response.json({ ok: true });
    return Response.json(library());
  });
  screen.nodes.get('message-text').value = 'Keep going gently.';

  await screen.nodes.get('message-form').listeners.submit({ preventDefault() {} });

  const save = screen.requests.find(request => request.method === 'POST');
  assert.equal(save.path, '/api/messages?category=motivation');
  assert.deepEqual(save.body, {
    text: 'Keep going gently.',
    active: true,
    days: ['ALL'],
    periods: ['ALL'],
  });
  assert.equal(screen.requests.filter(request => request.method === 'GET').length, 2);
  assert.equal(screen.nodes.get('message-category').disabled, false);
  assert.equal(screen.submit.disabled, false);
});

test('a slower category response cannot replace the category selected afterward', async () => {
  const pendingLoads = new Map();
  const screen = await page(async request => {
    if (request.path === '/api/messages') return Response.json(library());
    return new Promise(resolve => { pendingLoads.set(request.path, resolve); });
  });
  const category = screen.nodes.get('message-category');

  category.value = 'rest';
  category.listeners.change();
  category.value = 'focus';
  category.listeners.change();

  pendingLoads.get('/api/messages?category=rest')(Response.json(library({
    category: 'rest',
    messages: [{ id: 'old', text: 'Rest now.', active: true, days: ['ALL'], periods: ['ALL'] }],
  })));
  await settle();

  assert.equal(category.value, 'focus');
  assert.equal(screen.nodes.get('messages-summary').textContent, '0 personal messages');

  pendingLoads.get('/api/messages?category=focus')(Response.json(library({
    category: 'focus',
    messages: [{ id: 'new', text: 'Focus gently.', active: true, days: ['ALL'], periods: ['ALL'] }],
  })));
  await settle();

  assert.equal(category.value, 'focus');
  assert.equal(screen.nodes.get('messages-summary').textContent, '1 personal message');
  assert.equal(screen.nodes.get('message-list').childNodes[0].childNodes[0].childNodes[0].textContent, 'Focus gently.');
});

test('category tests are single-flight and restore the action after failure', async () => {
  let finishTest;
  const screen = await page(async request => {
    if (request.path === '/api/actions') return new Promise(resolve => { finishTest = resolve; });
    return Response.json(library());
  });
  const sendTest = screen.nodes.get('message-test').listeners.click;

  const pending = sendTest();
  sendTest();

  assert.equal(screen.requests.filter(request => request.path === '/api/actions').length, 1);
  assert.equal(screen.nodes.get('message-test').disabled, true);
  assert.equal(screen.nodes.get('message-test').attributes['aria-busy'], 'true');

  finishTest(Response.json({ error: 'Delivery is temporarily unavailable.' }, { status: 503 }));
  await pending;

  assert.equal(screen.nodes.get('message-test').disabled, false);
  assert.equal(screen.nodes.get('message-test').attributes['aria-busy'], undefined);
  assert.equal(screen.nodes.get('messages-status').textContent, 'Delivery is temporarily unavailable.');
  assert.equal(screen.nodes.get('messages-status').classList.contains('is-error'), true);
});

test('message category loads ignore stale responses', () => {
  assert.match(source, /const request = \+\+loadRequest/);
  assert.match(source, /if \(request !== loadRequest\) return/);
  assert.match(source, /if \(request === loadRequest\) showStatus/);
});

test('unsaved messages are protected from accidental workflow changes', () => {
  assert.match(source, /form\.dataset\.dirty = 'true'/);
  assert.match(source, /Discard this unsaved message and change categories/);
  assert.match(source, /Discard this unsaved message and edit another one/);
  assert.match(source, /mhm:before-logout/);
  assert.match(source, /beforeunload/);
});

test('category test action is explicit and single-flight', () => {
  assert.match(html, />Send category test</);
  assert.match(source, /if \(testButton\.disabled\) return/);
  assert.match(source, /testButton\.setAttribute\('aria-busy', 'true'\)/);
  assert.match(source, /testButton\.removeAttribute\('aria-busy'\)/);
});
