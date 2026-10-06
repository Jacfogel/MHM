import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';

const source = await readFile(new URL('./settings.js', import.meta.url), 'utf8');
const helperSource = `${source.slice(0, source.indexOf('(() =>'))}\nthis.helpers = MHMSettingsInput;`;
const context = vm.createContext({});
vm.runInContext(helperSource, context);

function element(tagName = 'div') {
  const classes = new Set();
  return {
    tagName: tagName.toUpperCase(),
    id: '',
    hidden: false,
    disabled: false,
    textContent: '',
    value: '',
    checked: false,
    childNodes: [],
    parentElement: null,
    attributes: {},
    dataset: {},
    listeners: {},
    get children() { return this.childNodes; },
    classList: {
      add(...names) { for (const name of names) classes.add(name); },
      remove(...names) { for (const name of names) classes.delete(name); },
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
    replaceChildren(...children) {
      this.childNodes = [];
      this.append(...children);
    },
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
        if (item === 'input' || item === 'select' || item === 'textarea' || item === 'button') return node.tagName === item.toUpperCase();
        if (item === '[data-settings-static]') return Object.hasOwn(node.dataset, 'settingsStatic');
        const attribute = item.match(/^\[([^=]+)="([^"]+)"\]$/);
        return attribute ? node.getAttribute(attribute[1]) === attribute[2] : false;
      });
      const visit = child => {
        if (matchesSelector(child)) matches.push(child);
        for (const grandchild of child.childNodes) visit(grandchild);
      };
      for (const child of this.childNodes) visit(child);
      return matches;
    },
    querySelector(selector) { return this.querySelectorAll(selector)[0] || null; },
    contains(candidate) {
      if (this === candidate) return true;
      return this.childNodes.some(child => child.contains(candidate));
    },
    replaceWith(replacement) {
      if (!this.parentElement) return;
      const index = this.parentElement.childNodes.indexOf(this);
      if (index >= 0) {
        replacement.parentElement = this.parentElement;
        this.parentElement.childNodes[index] = replacement;
      }
    },
    remove() {
      if (!this.parentElement) return;
      this.parentElement.childNodes = this.parentElement.childNodes.filter(child => child !== this);
      this.parentElement = null;
    },
    focus() { this.focused = true; },
    scrollIntoView(options) { this.scrollOptions = options; },
  };
}

function settingsData(overrides = {}) {
  const data = {
    sections: {
      profile: {
        preferred_name: 'River', date_of_birth: '', pronouns: [], gender_identity: [], interests: [], goals: [],
        activities_for_encouragement: [], health_conditions: [], medications_treatments: [],
        allergies_sensitivities: [], reminders_needed: [], notes_for_ai: [], loved_ones: [],
      },
      delivery: { timezone: 'America/Regina', channel: 'email' },
      phrases: {
        tonight_start_time: '18:00', after_work_school_time: '17:00',
        time_of_day_defaults: { morning: '09:00', afternoon: '14:00', evening: '18:00', night: '21:00' },
        weekend_this_week_means_coming_week: true,
      },
      messages: { enabled: false, categories: [], periods: {} },
      tasks: { enabled: true, periods: {}, recurring: {}, custom_templates: {} },
      checkins: { enabled: true, periods: {}, questions: {}, custom_questions: {}, min_questions: 1, max_questions: 1 },
    },
    revisions: Object.fromEntries(['profile', 'delivery', 'phrases', 'messages', 'tasks', 'checkins'].map(section => [section, `${section}-v1`])),
    options: {
      timezones: ['America/Regina'], categories: [], questions: {}, question_category_map: {}, question_categories: {},
    },
    available_message_periods: {},
    discord_linked: false,
  };
  return { ...data, ...overrides };
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

async function settingsPage(fetchImpl, { confirm = () => true } = {}) {
  const status = element('p');
  const retry = element('button');
  retry.hidden = true;
  const nav = element('nav');
  const panels = element('div');
  const settings = element('section');
  const accountContent = element('div');
  const accountButton = element('button');
  accountButton.setAttribute('data-settings-panel', 'account');
  accountButton.setAttribute('aria-controls', 'settings-account');
  const integrationsButton = element('button');
  integrationsButton.setAttribute('data-settings-panel', 'integrations');
  integrationsButton.setAttribute('aria-controls', 'settings-integrations');
  nav.append(accountButton, integrationsButton);
  const accountPanel = element('section');
  accountPanel.setAttribute('id', 'settings-account');
  accountPanel.setAttribute('data-settings-static', '');
  const integrationsPanel = element('section');
  integrationsPanel.setAttribute('id', 'settings-integrations');
  integrationsPanel.setAttribute('data-settings-static', '');
  panels.append(accountPanel, integrationsPanel);
  const fixed = new Map([
    ['settings-status', status], ['settings-retry', retry], ['settings-nav', nav], ['settings-panels', panels],
    ['settings', settings], ['account-content', accountContent],
  ]);
  const roots = [nav, panels, settings, accountContent];
  const findId = (node, id) => {
    if (node.id === id) return node;
    for (const child of node.childNodes) {
      const found = findId(child, id);
      if (found) return found;
    }
    return null;
  };
  const document = {
    getElementById(id) { return fixed.get(id) || roots.map(root => findId(root, id)).find(Boolean) || null; },
    createElement(tagName) { return element(tagName); },
  };
  const requests = [];
  const assigned = [];
  const replaced = [];
  const alerts = [];
  const window = new EventTarget();
  window.confirm = confirm;
  window.alert = message => alerts.push(message);
  window.matchMedia = () => ({ matches: false });
  vm.runInContext(source, vm.createContext({
    document,
    window,
    Event,
    URLSearchParams,
    crypto: { randomUUID: () => '00000000-0000-4000-8000-000000000001' },
    location: {
      hash: '', search: '',
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
  return { document, status, retry, nav, panels, accountContent, requests, assigned, replaced, alerts, window };
}

test('settings load every editable section and select the profile by default', async () => {
  const screen = await settingsPage(async () => Response.json(settingsData()));

  assert.equal(screen.status.textContent, '');
  assert.equal(screen.retry.hidden, true);
  assert.equal(screen.nav.children.length, 8);
  assert.equal(screen.panels.children.length, 8);
  assert.equal(screen.document.getElementById('settings-profile').hidden, false);
  assert.equal(screen.document.getElementById('settings-delivery').hidden, true);
  assert.equal(screen.document.getElementById('preferred-name').value, 'River');
  assert.equal(screen.document.getElementById('timezone').value, 'America/Regina');
});

test('saving profile settings locks all forms and submits the current revision', async () => {
  let finishSave;
  const initial = settingsData();
  const screen = await settingsPage(async request => {
    if (request.method === 'GET') return Response.json(initial);
    return new Promise(resolve => { finishSave = resolve; });
  });
  const form = screen.document.getElementById('settings-profile');
  screen.document.getElementById('preferred-name').value = 'Brook';
  form.listeners.input();

  const saving = form.listeners.submit({ preventDefault() {} });

  assert.equal(screen.document.getElementById('preferred-name').disabled, true);
  assert.equal(findByText(form, 'Saving…').textContent, 'Saving…');
  assert.equal(screen.requests.at(-1).body.section, 'profile');
  assert.equal(screen.requests.at(-1).body.revision, 'profile-v1');
  assert.equal(screen.requests.at(-1).body.values.preferred_name, 'Brook');

  const saved = settingsData();
  saved.revisions.profile = 'profile-v2';
  finishSave(Response.json(saved));
  await saving;

  assert.equal(form.dataset.dirty, 'false');
  assert.equal(screen.document.getElementById('preferred-name').disabled, false);
  assert.equal(findByText(form, 'Changes saved').textContent, 'Changes saved');
});

test('a settings conflict keeps the form usable and offers a section reload', async () => {
  const screen = await settingsPage(async request => (
    request.method === 'GET'
      ? Response.json(settingsData())
      : Response.json({ error: 'These settings changed in another session.' }, { status: 409 })
  ));
  const form = screen.document.getElementById('settings-profile');

  await form.listeners.submit({ preventDefault() {} });

  const reload = findByText(form, 'Reload this section');
  assert.equal(reload.hidden, false);
  assert.equal(findByText(form, 'These settings changed in another session.').classList.contains('is-error'), true);
  assert.equal(screen.document.getElementById('preferred-name').disabled, false);
});

test('saving feature settings marks first-run setup complete', async () => {
  const screen = await settingsPage(async request => (
    request.method === 'GET' ? Response.json(settingsData()) : Response.json(settingsData())
  ));
  const form = screen.document.getElementById('settings-tasks');

  await form.listeners.submit({ preventDefault() {} });

  const save = screen.requests.find(request => request.method === 'POST');
  assert.equal(save.body.section, 'tasks');
  assert.equal(save.body.complete_setup, true);
  assert.deepEqual(save.body.values.periods, {});
  assert.equal(save.body.values.enabled, true);
});

test('unsaved settings can prevent logout until the user decides what to do', async () => {
  const screen = await settingsPage(async () => Response.json(settingsData()), { confirm: () => false });
  const form = screen.document.getElementById('settings-profile');
  form.listeners.input();
  const logout = new Event('mhm:before-logout', { cancelable: true });

  screen.window.dispatchEvent(logout);

  assert.equal(form.dataset.dirty, 'true');
  assert.equal(logout.defaultPrevented, true);
});

test('an expired settings session hides account data and returns to login', async () => {
  const screen = await settingsPage(async () => Response.json({ error: 'expired' }, { status: 401 }));

  assert.equal(screen.accountContent.hidden, true);
  assert.deepEqual(screen.replaced, ['login.html']);
  assert.equal(screen.status.textContent, 'Please log in again.');
  assert.equal(screen.retry.hidden, false);
});

test('profile entries accept lines, commas, and semicolons', () => {
  assert.deepEqual(
    [...context.helpers.profileEntries('walking, reading; music\nfamily\n\n')],
    ['walking', 'reading', 'music', 'family'],
  );
});

test('settings collections must use the current schema', () => {
  assert.throws(() => context.helpers.record(undefined), /current object format/);
  assert.throws(() => context.helpers.record(null), /current object format/);
  assert.throws(() => context.helpers.list(undefined), /current list format/);
  assert.throws(() => context.helpers.list({}), /current list format/);
  assert.throws(() => context.helpers.profileEntries(null), /must be text/);
});

test('standard check-in questions are grouped by category', () => {
  const groups = context.helpers.questionGroups(
    { mood: 'Mood', stress: 'Stress', hydration: 'Hydration', custom_one: 'Custom' },
    { custom_one: {} },
    { mood: 'mood', stress: 'mood', hydration: 'health' },
    { mood: { name: 'Mood', description: 'Feelings' }, health: { name: 'Health' } },
  );
  assert.deepEqual(
    JSON.parse(JSON.stringify(groups)),
    [
      { key: 'mood', name: 'Mood', description: 'Feelings', questions: [{ key: 'mood', label: 'Mood' }, { key: 'stress', label: 'Stress' }] },
      { key: 'health', name: 'Health', description: '', questions: [{ key: 'hydration', label: 'Hydration' }] },
    ],
  );
});

test('clicking date and time inputs opens the native picker when available', () => {
  let opened = 0;
  context.helpers.openPicker({ disabled: false, readOnly: false, showPicker() { opened++; } });
  context.helpers.openPicker({ disabled: true, readOnly: false, showPicker() { opened++; } });
  context.helpers.openPicker({ disabled: false, readOnly: true, showPicker() { opened++; } });
  assert.equal(opened, 1);
});

test('date and time inputs open on the initial pointer action', () => {
  let opened = 0;
  const listeners = {};
  const input = {
    disabled: false,
    readOnly: false,
    showPicker() { opened++; },
    addEventListener(type, listener) { listeners[type] = listener; },
  };
  context.helpers.bindPicker(input);
  listeners.pointerdown({ button: 2 });
  assert.equal(opened, 0);
  listeners.pointerdown({ button: 0 });
  assert.equal(opened, 1);
});

test('changing settings sections returns to the settings heading', () => {
  let options;
  context.helpers.scrollToSection({ scrollIntoView(value) { options = value; } });
  assert.deepEqual({ ...options }, { behavior: 'smooth', block: 'start' });
  context.helpers.scrollToSection({ scrollIntoView(value) { options = value; } }, true);
  assert.deepEqual({ ...options }, { behavior: 'auto', block: 'start' });
});

test('signed-in page logos return to home', async () => {
  for (const page of ['home', 'app', 'tasks', 'notes', 'messages', 'insights', 'setup']) {
    const html = await readFile(new URL(`./${page}.html`, import.meta.url), 'utf8');
    assert.match(html, /class="brand" href="home\.html" aria-label="MHM home"/);
  }
});

test('feature details and custom check-in controls are present', async () => {
  assert.match(source, /details\.disabled = !enabled\.checked/);
  assert.match(source, /\+ Add custom question/);
  assert.match(source, /custom_\$\{crypto\.randomUUID\(\)/);
  assert.match(source, /category === 'tasks'[\s\S]*'15:00'[\s\S]*'17:00'/);
  assert.match(source, /category === 'checkin'[\s\S]*'09:30'[\s\S]*'11:30'/);
  assert.match(source, /const customQuestions = MHMSettingsInput\.record\(values\.custom_questions\)/);
  assert.doesNotMatch(source, /completeSettingsData/);
});

test('task settings include an account-owned template editor', () => {
  assert.match(source, /function customTaskTemplateEditor/);
  assert.match(source, /\+ Add task template/);
  assert.match(source, /custom_\$\{crypto\.randomUUID\(\)/);
  assert.match(source, /custom_templates: customTemplates\.read\(\)/);
  assert.match(source, /task template followed by the underscored template name/);
});

test('important-person prompts distinguish roles from useful context', () => {
  assert.match(source, /Family, friend, partner, healthcare provider/);
  assert.match(source, /Lives nearby; calls every Sunday; helps with appointments/);
  assert.doesNotMatch(source, /Sister, caregiver, emergency contact/);
});
