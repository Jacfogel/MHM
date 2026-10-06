import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';

const source = await readFile(new URL('./tasks.js', import.meta.url), 'utf8');
const helperSource = `${source.slice(0, source.indexOf('(() =>'))}\nthis.helpers = MHMTaskInput;`;
const context = vm.createContext({});
vm.runInContext(helperSource, context);

function element(tagName = 'div') {
  const classes = new Set();
  return {
    tagName: tagName.toUpperCase(),
    id: '',
    name: '',
    type: '',
    hidden: false,
    disabled: false,
    checked: false,
    textContent: '',
    value: '',
    className: '',
    childNodes: [],
    parentElement: null,
    attributes: {},
    dataset: {},
    listeners: {},
    get children() { return this.childNodes; },
    classList: {
      add(name) { classes.add(name); },
      remove(name) { classes.delete(name); },
      toggle(name, force) {
        if (force === undefined ? !classes.has(name) : force) classes.add(name);
        else classes.delete(name);
      },
      contains(name) { return classes.has(name); },
    },
    append(...children) {
      for (const child of children) {
        child.parentElement = this;
        this.childNodes.push(child);
      }
    },
    replaceChildren(...children) { this.childNodes = []; this.append(...children); },
    addEventListener(type, listener) { this.listeners[type] = listener; },
    dispatchEvent(event) { this.listeners[event.type]?.(event); return !event.defaultPrevented; },
    setAttribute(name, value) {
      this.attributes[name] = String(value);
      if (name === 'id') this.id = String(value);
      if (name.startsWith('data-')) {
        const key = name.slice(5).replace(/-([a-z])/g, (_match, letter) => letter.toUpperCase());
        this.dataset[key] = String(value);
      }
    },
    getAttribute(name) { return this.attributes[name] ?? null; },
    removeAttribute(name) { delete this.attributes[name]; },
    querySelectorAll(selector) {
      const matches = [];
      const selectors = selector.split(',').map(item => item.trim());
      const matchesSelector = node => selectors.some(item => {
        if (item === '.task-reminder-row') return node.className === 'task-reminder-row';
        if (item === 'strong') return node.tagName === 'STRONG';
        if (item === 'input') return node.tagName === 'INPUT';
        const typed = item.match(/^(input|button)\[type="([^"]+)"\]$/);
        return typed ? node.tagName === typed[1].toUpperCase() && node.type === typed[2] : false;
      });
      const visit = child => {
        if (matchesSelector(child)) matches.push(child);
        for (const grandchild of child.childNodes) visit(grandchild);
      };
      for (const child of this.childNodes) visit(child);
      return matches;
    },
    querySelector(selector) { return this.querySelectorAll(selector)[0] || null; },
    contains(candidate) { return this === candidate || this.childNodes.some(child => child.contains(candidate)); },
    closest(selector) {
      if (selector.includes(this.className)) return this;
      return this.parentElement?.closest(selector) || null;
    },
    focus() { this.focused = true; },
    remove() {
      if (!this.parentElement) return;
      this.parentElement.childNodes = this.parentElement.childNodes.filter(child => child !== this);
      this.parentElement = null;
    },
    showModal() { this.open = true; },
    close() { this.open = false; this.listeners.close?.(new Event('close')); },
    reset() {},
  };
}

function task(overrides = {}) {
  return {
    id: 'task-1', title: 'Pack lunch', description: 'Use the blue container', priority: 'medium',
    due_date: '2026-10-07', due_time: '08:00', tags: ['home'], reminders: [], recurrence: null,
    ...overrides,
  };
}

function taskResult(tasks = [], extras = {}) {
  return { tasks, tags: ['home', 'health'], due_soon_count: tasks.length, ...extras };
}

function allText(node) {
  return [node.textContent, ...node.childNodes.flatMap(allText)].filter(Boolean).join(' ');
}

function findByText(root, text) {
  if (root.textContent === text) return root;
  for (const child of root.childNodes) {
    const found = findByText(child, text);
    if (found) return found;
  }
  return null;
}

async function settle() {
  await new Promise(resolve => setImmediate(resolve));
  await new Promise(resolve => setImmediate(resolve));
}

async function tasksPage(fetchImpl, { confirm = () => true } = {}) {
  const ids = [
    'tasks-status', 'tasks-workspace', 'task-list', 'task-empty', 'tasks-count', 'task-list-summary',
    'task-create-form', 'task-due-soon', 'task-select-all', 'task-selected-count',
    'task-bulk-priority-controls', 'task-bulk-priority', 'task-bulk-priority-apply',
    'task-bulk-primary', 'task-bulk-delete', 'task-title', 'task-description', 'task-due-date',
    'task-due-time', 'task-priority', 'task-recurrence', 'task-recurrence-options',
    'task-custom-recurrence', 'task-recurrence-interval', 'task-recurrence-unit',
    'task-repeat-after-completion', 'task-tags', 'task-existing-tag', 'task-extra-fields',
    'task-more-options', 'task-reminder-list', 'task-add-reminder', 'task-template',
  ];
  const nodes = new Map(ids.map(id => [id, element()]));
  nodes.get('tasks-workspace').hidden = true;
  const emptyStrong = element('strong');
  nodes.get('task-empty').append(emptyStrong);
  nodes.get('task-priority').value = 'medium';
  nodes.get('task-recurrence-interval').value = '1';
  nodes.get('task-recurrence-unit').value = 'daily';
  nodes.get('task-repeat-after-completion').checked = true;
  const submit = element('button');
  submit.type = 'submit';
  const createForm = nodes.get('task-create-form');
  createForm.querySelector = selector => selector === 'button[type="submit"]' ? submit : null;
  createForm.reset = () => {
    for (const id of ['task-title', 'task-description', 'task-due-date', 'task-due-time', 'task-tags', 'task-recurrence']) nodes.get(id).value = '';
    nodes.get('task-priority').value = 'medium';
  };
  const tabs = ['active', 'completed'].map(taskView => {
    const tab = element('button');
    tab.dataset.taskView = taskView;
    return tab;
  });
  const body = element('body');
  const roots = [...nodes.values(), body];
  const findId = (node, id) => {
    if (node.id === id) return node;
    for (const child of node.childNodes) {
      const found = findId(child, id);
      if (found) return found;
    }
    return null;
  };
  const document = {
    body,
    getElementById(id) { return nodes.get(id) || roots.map(root => findId(root, id)).find(Boolean) || null; },
    createElement(tagName) { return element(tagName); },
    createTextNode(value) { const node = element('#text'); node.textContent = value; return node; },
    querySelectorAll(selector) {
      if (selector === '[data-task-view]') return tabs;
      if (selector === 'input[type="date"], input[type="time"]') return [nodes.get('task-due-date'), nodes.get('task-due-time')];
      return [];
    },
    querySelector(selector) {
      if (selector === 'input[name="quick_reminders"]:checked') return null;
      return null;
    },
  };
  function Option(label, value) {
    const option = element('option'); option.textContent = label; option.value = value; return option;
  }
  class FormData {
    get(name) {
      return {
        title: nodes.get('task-title').value,
        description: nodes.get('task-description').value,
        due_date: nodes.get('task-due-date').value,
        due_time: nodes.get('task-due-time').value,
        priority: nodes.get('task-priority').value,
        tags: nodes.get('task-tags').value,
      }[name];
    }
    getAll(name) { return name === 'quick_reminders' ? [] : []; }
  }
  const requests = [];
  const navigation = [];
  const window = new EventTarget();
  window.confirm = confirm;
  vm.runInContext(source, vm.createContext({
    document, window, Event, FormData, Option,
    location: { replace(url) { navigation.push(url); } },
    fetch: async (path, options) => {
      const request = { path, method: options.method, body: options.body ? JSON.parse(options.body) : undefined };
      requests.push(request);
      return fetchImpl(request);
    },
  }));
  await settle();
  return { nodes, tabs, body, requests, navigation, window, submit };
}

test('task list renders due details, tags, and the due-soon summary', async () => {
  const screen = await tasksPage(async request => (
    request.path === '/api/task-templates' ? Response.json({ templates: [] }) : Response.json(taskResult([task()]))
  ));

  assert.equal(screen.nodes.get('tasks-workspace').hidden, false);
  assert.equal(screen.nodes.get('tasks-count').textContent, '1 active task');
  assert.equal(screen.nodes.get('task-due-soon').hidden, false);
  assert.match(allText(screen.nodes.get('task-list').childNodes[0]), /Pack lunch Use the blue container Due 2026-10-07 at 08:00 medium Tags: home/);
});

test('creating a recurring task sends normalized fields and reloads the list', async () => {
  let created = false;
  const screen = await tasksPage(async request => {
    if (request.path === '/api/task-templates') return Response.json({ templates: [] });
    if (request.method === 'POST') { created = true; return Response.json({ ok: true }); }
    return Response.json(taskResult(created ? [task({ title: 'Water plants' })] : []));
  });
  screen.nodes.get('task-title').value = '  Water plants  ';
  screen.nodes.get('task-description').value = 'Use rain water.';
  screen.nodes.get('task-due-date').value = '2026-10-08';
  screen.nodes.get('task-priority').value = 'high';
  screen.nodes.get('task-recurrence').value = 'custom';
  screen.nodes.get('task-recurrence-interval').value = '2';
  screen.nodes.get('task-recurrence-unit').value = 'weekly';
  screen.nodes.get('task-tags').value = 'home, plants';

  await screen.nodes.get('task-create-form').listeners.submit({ preventDefault() {} });

  const create = screen.requests.find(request => request.method === 'POST');
  assert.deepEqual(create.body, {
    title: 'Water plants', description: 'Use rain water.', due_date: '2026-10-08', due_time: null,
    priority: 'high', recurrence_pattern: 'weekly', recurrence_interval: 2,
    repeat_after_completion: true, tags: ['home', 'plants'], reminder_periods: [], quick_reminders: [],
  });
  assert.equal(screen.nodes.get('tasks-count').textContent, '1 active task');
  assert.equal(screen.submit.disabled, false);
});

test('failed task creation preserves the draft and restores the submit action', async () => {
  const screen = await tasksPage(async request => {
    if (request.path === '/api/task-templates') return Response.json({ templates: [] });
    if (request.method === 'POST') return Response.json({ error: 'Task could not be saved.' }, { status: 503 });
    return Response.json(taskResult());
  });
  screen.nodes.get('task-title').value = 'Keep this draft';

  await screen.nodes.get('task-create-form').listeners.submit({ preventDefault() {} });

  assert.equal(screen.nodes.get('task-title').value, 'Keep this draft');
  assert.equal(screen.submit.disabled, false);
  assert.equal(screen.nodes.get('tasks-status').textContent, 'Task could not be saved.');
  assert.equal(screen.nodes.get('tasks-status').classList.contains('is-error'), true);
});

test('editing a task sends changes and recovers cleanly from a failed request', async () => {
  const screen = await tasksPage(async request => {
    if (request.path === '/api/task-templates') return Response.json({ templates: [] });
    if (request.method === 'PATCH') return Response.json({ error: 'Edit conflict.' }, { status: 409 });
    return Response.json(taskResult([task()]));
  });
  findByText(screen.nodes.get('task-list'), 'Edit').listeners.click();
  const dialog = screen.body.childNodes[0];
  const form = dialog.childNodes.find(child => child.tagName === 'FORM');
  const title = screen.body.querySelectorAll('input').find(input => input.id === 'edit-title');
  title.value = 'Pack breakfast';

  await form.listeners.submit({ preventDefault() {} });

  const edit = screen.requests.find(request => request.method === 'PATCH');
  assert.equal(edit.path, '/api/tasks/task-1');
  assert.equal(edit.body.title, 'Pack breakfast');
  assert.equal(findByText(form, 'Save changes').disabled, false);
  assert.equal(screen.nodes.get('tasks-status').textContent, 'Edit conflict.');
  assert.equal(dialog.open, true);
});

test('a stale completed-task response cannot replace the active view', async () => {
  let activeLoads = 0;
  let finishCompleted;
  let finishActive;
  const screen = await tasksPage(async request => {
    if (request.path === '/api/task-templates') return Response.json({ templates: [] });
    if (request.path === '/api/tasks?status=active' && activeLoads++ === 0) {
      return Response.json(taskResult([task({ title: 'Initial active task' })]));
    }
    if (request.path === '/api/tasks?status=completed') {
      return new Promise(resolve => { finishCompleted = resolve; });
    }
    return new Promise(resolve => { finishActive = resolve; });
  });

  screen.tabs[1].listeners.click();
  screen.tabs[0].listeners.click();

  finishCompleted(Response.json(taskResult([task({ title: 'Old completed task' })])));
  await settle();
  assert.match(allText(screen.nodes.get('task-list')), /Initial active task/);

  finishActive(Response.json(taskResult([task({ title: 'Current active task' })])));
  await settle();
  assert.match(allText(screen.nodes.get('task-list')), /Current active task/);
  assert.doesNotMatch(allText(screen.nodes.get('task-list')), /Old completed task/);
});

test('an unsaved task draft can prevent logout', async () => {
  const screen = await tasksPage(async request => (
    request.path === '/api/task-templates' ? Response.json({ templates: [] }) : Response.json(taskResult())
  ), { confirm: () => false });
  screen.nodes.get('task-title').value = 'Do not lose this';
  const logout = new Event('mhm:before-logout', { cancelable: true });

  screen.window.dispatchEvent(logout);

  assert.equal(logout.defaultPrevented, true);
});

test('task help asks for smaller steps instead of replacing the title', () => {
  assert.match(source, /Suggest smaller steps/);
  assert.match(source, /\/breakdown/);
  assert.match(source, /'subtasks'/);
  assert.match(source, /task-step-title/);
  assert.match(source, /Make this its own task/);
  assert.match(source, /restore_steps/);
  assert.doesNotMatch(source, /simplify-title/);
});

test('existing task tags append without duplicates', () => {
  assert.equal(context.helpers.withTag('health, home', 'work'), 'health, home, work');
  assert.equal(context.helpers.withTag('health, home', 'HEALTH'), 'health, home');
  assert.equal(context.helpers.withTag('', 'personal'), 'personal');
});

test('blank template selection resets all create-form fields', () => {
  assert.match(source, /const templateId = event\.target\.value;[\s\S]*resetCreateForm\(\);[\s\S]*if \(!template\)/);
  assert.match(source, /function resetCreateForm\(\) \{[\s\S]*createForm\.reset\(\);[\s\S]*task-reminder-list[\s\S]*setExtraFieldsOpen\(false\)/);
});

test('extra create fields stay collapsed until More options is opened', () => {
  assert.match(source, /function setExtraFieldsOpen\(open\) \{[\s\S]*extraFields\.hidden = !open;[\s\S]*Fewer options/);
  assert.match(source, /moreOptions\.addEventListener\('click', \(\) => setExtraFieldsOpen\(extraFields\.hidden\)\)/);
  assert.match(source, /if \(!template\) \{ setExtraFieldsOpen\(false\);[\s\S]*setExtraFieldsOpen\(true\);/);
});

test('selected active tasks can receive one priority in bulk', async () => {
  const html = await readFile(new URL('./tasks.html', import.meta.url), 'utf8');
  assert.match(html, /id="task-bulk-priority"/);
  assert.match(html, /id="task-bulk-priority-apply"/);
  assert.match(source, /runBulk\('priority', \{ priority: bulkPriority\.value \}\)/);
  assert.match(source, /bulkPriorityControls\.hidden = view !== 'active'/);
  assert.match(source, /action !== 'priority' && !window\.confirm/);
});

test('task list supports selecting or clearing every visible task', async () => {
  const html = await readFile(new URL('./tasks.html', import.meta.url), 'utf8');
  assert.match(html, /id="task-select-all"/);
  assert.match(source, /tasks\.every\(task => selected\.has\(task\.id\)\)/);
  assert.match(source, /allSelected \? 'Clear selection' : 'Select all'/);
  assert.match(source, /tasks\.forEach\(task => selected\.add\(task\.id\)\)/);
});

test('task loading ignores responses for an older view', () => {
  assert.match(source, /const request = \+\+loadRequest/);
  assert.match(source, /if \(request !== loadRequest \|\| requestedView !== view\) return/);
});

test('due-soon summary stays quiet when it has nothing useful to say', () => {
  assert.match(source, /dueSoon\.hidden = view !== 'active' \|\| dueSoonCount === 0/);
});

test('task drafts and changed edit dialogs are protected from accidental dismissal', () => {
  assert.match(source, /function hasTaskDraft\(\)/);
  assert.match(source, /Discard your unsaved task changes/);
  assert.match(source, /mhm:before-logout/);
  assert.match(source, /beforeunload/);
  assert.match(source, /dialog\.addEventListener\('cancel'/);
  assert.match(source, /task-reminder-add, \.task-reminder-remove/);
});
