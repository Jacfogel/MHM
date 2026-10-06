import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import vm from 'node:vm';

const source = await readFile(new URL('./checkin.js', import.meta.url), 'utf8');
const css = await readFile(new URL('./styles.css', import.meta.url), 'utf8');

function element(tagName = 'div') {
  const classes = new Set();
  return {
    tagName: tagName.toUpperCase(),
    hidden: false,
    disabled: false,
    textContent: '',
    value: '',
    childNodes: [],
    attributes: {},
    listeners: {},
    classList: {
      toggle(name, force) {
        if (force === undefined ? !classes.has(name) : force) classes.add(name);
        else classes.delete(name);
      },
      contains(name) { return classes.has(name); },
    },
    get childElementCount() { return this.childNodes.length; },
    setAttribute(name, value) { this.attributes[name] = value; },
    removeAttribute(name) { delete this.attributes[name]; },
    addEventListener(type, listener) { this.listeners[type] = listener; },
    appendChild(child) {
      this.childNodes.push(child);
      if (this.tagName === 'SELECT' && child.selected) this.value = child.value;
      return child;
    },
    append(...children) { this.childNodes.push(...children); },
    replaceChildren(...children) { this.childNodes = children; },
    querySelectorAll(selector) {
      const descendants = [];
      const visit = child => {
        if (selector === 'select' && child.tagName === 'SELECT') descendants.push(child);
        if (selector === '.checkin-sleep-row' && child.className === 'checkin-sleep-row') descendants.push(child);
        for (const grandchild of child.childNodes || []) visit(grandchild);
      };
      for (const child of this.childNodes) visit(child);
      return descendants;
    },
    focus() { this.focused = true; },
    remove() { this.removed = true; },
  };
}

async function settle() {
  await new Promise(resolve => setImmediate(resolve));
  await new Promise(resolve => setImmediate(resolve));
}

async function page(fetchImpl) {
  const ids = [
    'checkin-status', 'checkin-panel', 'checkin-progress', 'checkin-message', 'checkin-off',
    'checkin-form', 'checkin-choices', 'checkin-sleep', 'checkin-sleep-chunks',
    'checkin-sleep-add', 'checkin-answer-field', 'checkin-answer', 'checkin-save',
    'checkin-skip', 'checkin-cancel',
  ];
  const nodes = new Map(ids.map(id => [id, element(id === 'checkin-form' ? 'form' : 'div')]));
  const document = {
    getElementById(id) { return nodes.get(id); },
    createElement(tagName) { return element(tagName); },
  };
  const formControls = [
    nodes.get('checkin-answer'), nodes.get('checkin-save'), nodes.get('checkin-skip'),
    nodes.get('checkin-cancel'), nodes.get('checkin-sleep-add'),
  ];
  nodes.get('checkin-form').querySelectorAll = selector => (
    selector === 'button, input, select' ? formControls : []
  );
  const window = new EventTarget();
  let signedOut = 0;
  window.addEventListener('mhm:signed-out', () => { signedOut += 1; });
  const navigation = [];
  const requests = [];
  vm.runInContext(source, vm.createContext({
    document,
    window,
    Event,
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
  return { nodes, navigation, requests, signedOut: () => signedOut };
}

test('an idle check-in starts automatically and a scale answer completes it', async () => {
  const screen = await page(async request => {
    if (request.method === 'GET') {
      return Response.json({ enabled: true, active: false, completed_today: false });
    }
    if (request.body.action === 'start') {
      return Response.json({
        enabled: true,
        active: true,
        index: 1,
        total: 2,
        question_type: 'scale_1_5',
        message: 'How is your mood?',
      });
    }
    return Response.json({ enabled: true, active: false, completed: true, message: 'Thanks for checking in.' });
  });

  assert.deepEqual(screen.requests.map(request => request.body?.action), [undefined, 'start']);
  assert.equal(screen.nodes.get('checkin-progress').textContent, 'Question 1 of 2');
  assert.equal(screen.nodes.get('checkin-message').textContent, 'How is your mood?');
  assert.equal(screen.nodes.get('checkin-form').hidden, false);
  assert.equal(screen.nodes.get('checkin-answer-field').hidden, true);
  assert.equal(screen.nodes.get('checkin-choices').childElementCount, 5);

  await screen.nodes.get('checkin-choices').childNodes[3].listeners.click();

  assert.deepEqual(screen.requests.at(-1).body, { action: 'answer', answer: '4' });
  assert.equal(screen.nodes.get('checkin-form').hidden, true);
  assert.equal(screen.nodes.get('checkin-message').textContent, 'Thanks for checking in.');
});

test('sleep check-ins serialize up to three sleep periods', async () => {
  const screen = await page(async request => {
    if (request.method === 'GET') {
      return Response.json({
        enabled: true,
        active: true,
        index: 1,
        total: 1,
        question_type: 'time_pair',
        message: 'When did you sleep?',
      });
    }
    return Response.json({ enabled: true, active: false, completed: true, message: 'Sleep saved.' });
  });
  const sleepChunks = screen.nodes.get('checkin-sleep-chunks');

  screen.nodes.get('checkin-sleep-add').listeners.click();
  screen.nodes.get('checkin-sleep-add').listeners.click();

  assert.equal(screen.nodes.get('checkin-sleep').hidden, false);
  assert.equal(sleepChunks.childElementCount, 3);
  assert.equal(screen.nodes.get('checkin-sleep-add').hidden, true);

  screen.nodes.get('checkin-form').listeners.submit({ preventDefault() {} });
  await settle();

  assert.deepEqual(screen.requests.at(-1).body, {
    action: 'answer',
    answer: '11:00 PM-7:00 AM; 11:00 PM-7:00 AM; 11:00 PM-7:00 AM',
  });
  assert.equal(screen.nodes.get('checkin-message').textContent, 'Sleep saved.');
});

test('typed answers are trimmed and duplicate submissions are blocked while saving', async () => {
  let finishSaving;
  const screen = await page(async request => {
    if (request.method === 'GET') {
      return Response.json({
        enabled: true,
        active: true,
        index: 1,
        total: 1,
        question_type: 'optional_text',
        message: 'Anything else?',
      });
    }
    return new Promise(resolve => { finishSaving = resolve; });
  });
  screen.nodes.get('checkin-answer').value = '  A little tired  ';
  const submit = screen.nodes.get('checkin-form').listeners.submit;
  const event = { preventDefault() {} };

  submit(event);
  submit(event);

  assert.equal(screen.requests.length, 2);
  assert.deepEqual(screen.requests[1].body, { action: 'answer', answer: 'A little tired' });
  assert.equal(screen.nodes.get('checkin-form').attributes['aria-busy'], 'true');
  assert.equal(screen.nodes.get('checkin-answer').disabled, true);

  finishSaving(Response.json({ enabled: true, active: false, completed: true, message: 'Saved.' }));
  await settle();

  assert.equal(screen.nodes.get('checkin-form').attributes['aria-busy'], undefined);
  assert.equal(screen.nodes.get('checkin-answer').disabled, false);
});

test('an expired check-in session signs out without leaving private content visible', async () => {
  const screen = await page(async () => Response.json({ error: 'expired' }, { status: 401 }));

  assert.equal(screen.signedOut(), 1);
  assert.deepEqual(screen.navigation, ['login.html']);
  assert.equal(screen.nodes.get('checkin-panel').hidden, true);
  assert.equal(screen.nodes.get('checkin-status').textContent, 'Please log in again.');
  assert.equal(screen.nodes.get('checkin-status').classList.contains('is-error'), true);
});

test('the answer box clears whenever a check-in question is shown', () => {
  assert.match(source, /form\.hidden = !result\.active;\s*answer\.value = '';/);
});

test('scale and yes or no questions offer a one-tap answer', () => {
  assert.match(source, /type === 'scale_1_5'/);
  assert.match(source, /choiceButton\('Yes', 'yes'\)/);
  assert.match(source, /choiceButton\('No', 'no'\)/);
  assert.match(source, /const typed = type !== 'scale_1_5' && type !== 'yes_no' && !sleep/);
  assert.match(source, /Fell asleep/);
  assert.match(source, /Woke up/);
  assert.match(source, /answerField\.hidden = !typed/);
  assert.match(source, /type === 'time_pair'/);
});

test('check-in prompts keep the line break before the next question', () => {
  assert.match(css, /#checkin-message \{ white-space: pre-wrap; \}/);
});

test('check-in actions stay single-flight while an answer is saving', () => {
  assert.match(source, /if \(sending\) return/);
  assert.match(source, /form\.setAttribute\('aria-busy', 'true'\)/);
  assert.match(source, /form\.querySelectorAll\('button, input, select'\)/);
  assert.match(source, /finally \{\s*setBusy\(false\)/);
});
