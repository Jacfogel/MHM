import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import vm from 'node:vm';

const source = await readFile(new URL('./insights.js', import.meta.url), 'utf8');

function element(tagName = 'div') {
  const classes = new Set();
  return {
    tagName: tagName.toUpperCase(),
    hidden: false,
    disabled: false,
    textContent: '',
    value: '',
    className: '',
    childNodes: [],
    attributes: {},
    listeners: {},
    get children() { return this.childNodes; },
    classList: {
      add(name) { classes.add(name); },
      remove(name) { classes.delete(name); },
      contains(name) { return classes.has(name); },
    },
    append(...children) { this.childNodes.push(...children); },
    replaceChildren(...children) { this.childNodes = children; },
    setAttribute(name, value) { this.attributes[name] = value; },
    removeAttribute(name) { delete this.attributes[name]; },
    addEventListener(type, listener) { this.listeners[type] = listener; },
  };
}

async function settle() {
  await new Promise(resolve => setImmediate(resolve));
  await new Promise(resolve => setImmediate(resolve));
}

function insightData(days) {
  return {
    days,
    available: { total_checkins: 0 },
    wellness: {},
    mood: { error: 'No mood data' },
    energy: { error: 'No energy data' },
    completion: {},
    quantitative: {},
    sleep: { error: 'No sleep data' },
    habits: { habits: {} },
    history: [],
  };
}

async function page(fetchImpl) {
  const ids = [
    'insights-status', 'insights-content', 'insights-days', 'insights-refresh', 'checkin-request',
    'insights-summary', 'mood-energy', 'wellness-recommendations', 'sleep-detail', 'habit-detail',
    'checkin-history', 'insights-checkin-answer',
  ];
  const nodes = new Map(ids.map(id => [id, element()]));
  nodes.get('insights-days').value = '30';
  nodes.get('insights-content').hidden = true;
  const requests = [];
  const navigation = [];
  const window = new EventTarget();
  vm.runInContext(source, vm.createContext({
    document: {
      getElementById(id) { return nodes.get(id); },
      createElement(tagName) { return element(tagName); },
    },
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
  return { nodes, requests, navigation };
}

test('changing insight ranges keeps stale results hidden until the latest request finishes', async () => {
  const insightResponses = [];
  const screen = await page(async request => {
    if (request.path === '/api/account') return Response.json({ checkins_enabled: true });
    return new Promise(resolve => { insightResponses.push(resolve); });
  });
  screen.nodes.get('insights-days').value = '7';
  const latest = screen.nodes.get('insights-days').listeners.change();

  insightResponses[0](Response.json(insightData(30)));
  await settle();

  assert.equal(screen.nodes.get('insights-content').hidden, true);
  assert.equal(screen.nodes.get('insights-refresh').disabled, true);
  assert.equal(screen.nodes.get('insights-content').attributes['aria-busy'], 'true');

  insightResponses[1](Response.json(insightData(7)));
  await latest;

  assert.equal(screen.nodes.get('insights-content').hidden, false);
  assert.equal(screen.nodes.get('insights-refresh').disabled, false);
  assert.equal(screen.nodes.get('insights-content').attributes['aria-busy'], undefined);
  assert.equal(screen.nodes.get('insights-summary').childNodes[0].childNodes[2].textContent, 'Last 7 days');
});

test('requesting a check-in is single-flight and reports the queued result', async () => {
  let finishRequest;
  const screen = await page(async request => {
    if (request.path === '/api/account') return Response.json({ checkins_enabled: true });
    if (request.path.startsWith('/api/insights')) return Response.json(insightData(30));
    return new Promise(resolve => { finishRequest = resolve; });
  });
  const requestCheckin = screen.nodes.get('checkin-request').listeners.click;

  const pending = requestCheckin();
  requestCheckin();

  const actionRequests = screen.requests.filter(request => request.path === '/api/actions');
  assert.equal(actionRequests.length, 1);
  assert.deepEqual(actionRequests[0].body, { action: 'checkin_prompt' });
  assert.equal(screen.nodes.get('checkin-request').disabled, true);
  assert.equal(screen.nodes.get('checkin-request').attributes['aria-busy'], 'true');
  assert.equal(screen.nodes.get('insights-status').textContent, 'Queueing your check-in…');

  finishRequest(Response.json({ message: 'Your check-in is on the way.' }));
  await pending;

  assert.equal(screen.nodes.get('checkin-request').disabled, false);
  assert.equal(screen.nodes.get('checkin-request').attributes['aria-busy'], undefined);
  assert.equal(screen.nodes.get('insights-status').textContent, 'Your check-in is on the way.');
});

test('insight range changes ignore stale responses', () => {
  assert.match(source, /const request = \+\+loadRequest/);
  assert.match(source, /requestedDays !== days\.value/);
  assert.match(source, /content\.setAttribute\('aria-busy', 'true'\)/);
  assert.match(source, /content\.removeAttribute\('aria-busy'\)/);
});

test('check-in requests are explicit and single-flight', () => {
  assert.match(source, /if \(checkinRequest\.disabled\) return/);
  assert.match(source, /Queueing your check-in/);
  assert.match(source, /checkinRequest\.setAttribute\('aria-busy', 'true'\)/);
  assert.match(source, /checkinRequest\.removeAttribute\('aria-busy'\)/);
});
