import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import vm from 'node:vm';

const source = await readFile(new URL('./notes.js', import.meta.url), 'utf8');
const html = await readFile(new URL('./notes.html', import.meta.url), 'utf8');

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
    get firstChild() { return this.childNodes[0]; },
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
    dispatchEvent(event) { this.listeners[event.type]?.(event); return !event.defaultPrevented; },
    setAttribute(name, value) { this.attributes[name] = value; },
    removeAttribute(name) { delete this.attributes[name]; },
    querySelectorAll(selector) {
      const matches = [];
      const visit = child => {
        if (selector === '.notebook-item-row' && child.className === 'notebook-item-row') matches.push(child);
        for (const grandchild of child.childNodes || []) visit(grandchild);
      };
      for (const child of this.childNodes) visit(child);
      return matches;
    },
    querySelector(selector) {
      if (selector === 'input[type="text"]') return this.childNodes.find(child => child.tagName === 'INPUT' && child.type === 'text') || null;
      if (selector === 'input[type="checkbox"]') return this.childNodes.find(child => child.tagName === 'INPUT' && child.type === 'checkbox') || null;
      return null;
    },
    focus() { this.focused = true; },
    reset() {},
    remove() { this.removed = true; },
  };
}

async function settle() {
  await new Promise(resolve => setImmediate(resolve));
  await new Promise(resolve => setImmediate(resolve));
}

function noteResult(notes = [], tags = []) {
  return { notes, tags };
}

function savedNote(overrides = {}) {
  return {
    id: 'note-1',
    kind: 'note',
    status: 'active',
    title: 'Questions for my appointment',
    description: 'Ask about sleep.',
    tags: ['health'],
    pinned: false,
    ...overrides,
  };
}

function allText(node) {
  return [node.textContent, ...node.childNodes.flatMap(allText)].filter(Boolean).join(' ');
}

function findByText(node, text) {
  if (node.textContent === text) return node;
  for (const child of node.childNodes || []) {
    const match = findByText(child, text);
    if (match) return match;
  }
  return null;
}

async function page(fetchImpl, { confirm = () => true } = {}) {
  const ids = [
    'notes-status', 'notes-workspace', 'note-list', 'note-empty', 'note-empty-title',
    'note-empty-help', 'note-clear-filters', 'notes-count', 'note-create-form', 'entry-kind',
    'entry-description-field', 'entry-description-label', 'entry-list-field', 'entry-create-items',
    'entry-create-submit', 'entry-create-heading', 'entry-create-help', 'note-search',
    'note-tag-filter', 'note-existing-tag', 'note-tags', 'note-title', 'note-description',
    'entry-add-item', 'note-tabs', 'notes-refresh', 'note-extra-fields', 'note-more-options',
  ];
  const nodes = new Map(ids.map(id => [id, element()]));
  nodes.get('notes-workspace').hidden = true;
  nodes.get('entry-kind').value = 'note';
  nodes.get('entry-create-submit').append(element('#text'));
  const submit = nodes.get('entry-create-submit');
  const createForm = nodes.get('note-create-form');
  createForm.querySelector = selector => selector === 'button[type="submit"]' ? submit : null;
  createForm.reset = () => {
    nodes.get('entry-kind').value = 'note';
    nodes.get('note-title').value = '';
    nodes.get('note-description').value = '';
    nodes.get('note-tags').value = '';
  };
  const tabs = ['active', 'pinned', 'inbox', 'archived'].map(noteView => {
    const tab = element('button');
    tab.dataset.noteView = noteView;
    return tab;
  });
  const documentListeners = {};
  const document = {
    visibilityState: 'visible',
    body: { append() {} },
    getElementById(id) { return nodes.get(id); },
    createElement(tagName) { return element(tagName); },
    querySelectorAll(selector) { return selector === '[data-note-view]' ? tabs : []; },
    addEventListener(type, listener) { documentListeners[type] = listener; },
  };
  function Option(label, value) {
    const option = element('option');
    option.textContent = label;
    option.value = value;
    return option;
  }
  class FormData {
    get(name) {
      return {
        kind: nodes.get('entry-kind').value,
        title: nodes.get('note-title').value,
        description: nodes.get('note-description').value,
        tags: nodes.get('note-tags').value,
      }[name];
    }
  }
  const requests = [];
  const navigation = [];
  const window = new EventTarget();
  window.confirm = confirm;
  vm.runInContext(source, vm.createContext({
    document,
    window,
    Event,
    FormData,
    Option,
    URLSearchParams,
    location: { replace(url) { navigation.push(url); } },
    setTimeout(callback) { callback(); return 1; },
    clearTimeout() {},
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
  return { nodes, requests, navigation, window };
}

test('notebook entries load with their type, content, and tags', async () => {
  const screen = await page(async () => Response.json(noteResult([savedNote()], ['health', 'sleep'])));

  assert.equal(screen.nodes.get('notes-workspace').hidden, false);
  assert.equal(screen.nodes.get('notes-count').textContent, '1 active entry');
  assert.equal(screen.nodes.get('note-list').childNodes.length, 1);
  assert.match(allText(screen.nodes.get('note-list').childNodes[0]), /Note Questions for my appointment Ask about sleep\. Tags: health/);
  assert.equal(screen.nodes.get('note-existing-tag').childNodes.length, 3);
  assert.equal(screen.nodes.get('note-tag-filter').childNodes.length, 3);
});

test('creating a note sends normalized fields and reloads the notebook', async () => {
  let saved = false;
  const screen = await page(async request => {
    if (request.method === 'POST') {
      saved = true;
      return Response.json({ ok: true });
    }
    return Response.json(noteResult(saved ? [savedNote()] : [], ['health']));
  });
  screen.nodes.get('note-title').value = '  Questions for my appointment  ';
  screen.nodes.get('note-description').value = 'Ask about sleep.';
  screen.nodes.get('note-tags').value = 'health, sleep';

  await screen.nodes.get('note-create-form').listeners.submit({ preventDefault() {} });

  const create = screen.requests.find(request => request.method === 'POST');
  assert.equal(create.path, '/api/notes');
  assert.deepEqual(create.body, {
    kind: 'note',
    title: 'Questions for my appointment',
    tags: ['health', 'sleep'],
    description: 'Ask about sleep.',
  });
  assert.equal(screen.nodes.get('notes-count').textContent, '1 active entry');
  assert.equal(screen.nodes.get('entry-create-submit').disabled, false);
});

test('a failed note create keeps the draft and explains how to avoid a duplicate', async () => {
  const screen = await page(async request => {
    if (request.method === 'POST') {
      return Response.json(
        { error: 'MHM could not complete this request. Please try again.' },
        { status: 503 },
      );
    }
    return Response.json(noteResult());
  });
  screen.nodes.get('note-title').value = 'Keep this draft';
  screen.nodes.get('note-description').value = 'Important details';

  await screen.nodes.get('note-create-form').listeners.submit({ preventDefault() {} });

  assert.equal(screen.nodes.get('note-title').value, 'Keep this draft');
  assert.equal(screen.nodes.get('note-description').value, 'Important details');
  assert.equal(screen.nodes.get('entry-create-submit').disabled, false);
  assert.match(screen.nodes.get('notes-status').textContent, /could not confirm that your note was saved/i);
  assert.match(screen.nodes.get('notes-status').textContent, /draft is still here/i);
  assert.match(screen.nodes.get('notes-status').textContent, /Refresh the notebook to check/i);
});

test('a notebook load network failure gives a safe retry action', async () => {
  const screen = await page(async () => { throw new Error('Failed to fetch'); });

  assert.match(screen.nodes.get('notes-status').textContent, /could not load your notebook/i);
  assert.match(screen.nodes.get('notes-status').textContent, /entries were not changed/i);
  assert.match(screen.nodes.get('notes-status').textContent, /use Refresh/i);
  assert.doesNotMatch(screen.nodes.get('notes-status').textContent, /Failed to fetch/);
});

test('an uncertain archive result tells the user to verify the current section', async () => {
  const screen = await page(async request => {
    if (request.method === 'POST') throw new Error('connection reset');
    return Response.json(noteResult([savedNote()]));
  });
  const archive = findByText(screen.nodes.get('note-list'), 'Archive');

  await archive.listeners.click();

  assert.match(screen.nodes.get('notes-status').textContent, /could not confirm that this entry was archived/i);
  assert.match(screen.nodes.get('notes-status').textContent, /check its current section before trying again/i);
  assert.doesNotMatch(screen.nodes.get('notes-status').textContent, /connection reset/);
});

test('a stale notebook search cannot replace newer search results', async () => {
  const pending = new Map();
  const screen = await page(async request => {
    if (!request.path.includes('&q=')) return Response.json(noteResult());
    return new Promise(resolve => { pending.set(request.path, resolve); });
  });
  const search = screen.nodes.get('note-search');

  search.value = 'old';
  search.listeners.input();
  search.value = 'current';
  search.listeners.input();

  pending.get('/api/notes?status=active&q=old')(Response.json(noteResult([savedNote({ title: 'Old result' })])));
  await settle();
  assert.equal(screen.nodes.get('notes-count').textContent, '0 active entries');

  pending.get('/api/notes?status=active&q=current')(Response.json(noteResult([savedNote({ title: 'Current result' })])));
  await settle();
  assert.equal(screen.nodes.get('notes-count').textContent, '1 active entry');
  assert.match(allText(screen.nodes.get('note-list').childNodes[0]), /Current result/);
});

test('an unsaved notebook draft can block logout and navigation', async () => {
  const screen = await page(async () => Response.json(noteResult()), { confirm: () => false });
  screen.nodes.get('note-title').value = 'Do not lose this';
  const logout = new Event('mhm:before-logout', { cancelable: true });

  screen.window.dispatchEvent(logout);

  assert.equal(logout.defaultPrevented, true);
});

test('notebook create and edit forms provide an existing-tags picker', () => {
  assert.match(html, /id="note-existing-tag"/);
  assert.match(source, /populateTagPicker\(document\.getElementById\('note-existing-tag'\), existingTags\)/);
  assert.match(source, /bindTagPicker\(tags, existingTag\)/);
});

test('notebook tabs are active, pinned, inbox, and archived', () => {
  assert.match(html, /id="note-tabs"/);
  assert.match(html, /data-note-view="active"/);
  assert.match(html, /data-note-view="pinned"/);
  assert.match(html, /data-note-view="inbox"/);
  assert.match(html, /data-note-view="archived"/);
});

test('archived entries do not render a pinned quality', () => {
  assert.match(source, /note\.status === 'active' && note\.pinned/);
});

test('notebook loading ignores stale search and tab responses', () => {
  assert.match(source, /const request = \+\+loadRequest/);
  assert.match(source, /requestedView !== view/);
  assert.match(source, /requestedQuery !== search\.value\.trim\(\)/);
  assert.match(source, /requestedTag !== tagFilter\.value/);
});

test('empty notebook searches explain the result and can clear filters', () => {
  assert.match(html, /id="note-empty-title"/);
  assert.match(html, /id="note-clear-filters"/);
  assert.match(source, /No matching entries\./);
  assert.match(source, /search\.value = ''/);
  assert.match(source, /tagFilter\.value = ''/);
});

test('notebook drafts and changed edit dialogs are protected from accidental dismissal', () => {
  assert.match(source, /function hasNoteDraft\(\)/);
  assert.match(source, /Discard your unsaved notebook changes/);
  assert.match(source, /mhm:before-logout/);
  assert.match(source, /beforeunload/);
  assert.match(source, /dialog\.addEventListener\('cancel'/);
  assert.match(source, /notebook-item-remove, \.notebook-add-item/);
});
