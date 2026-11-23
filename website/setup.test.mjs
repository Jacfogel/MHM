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

async function page({ account = {
  preferred_name: 'Brook', timezone: 'America/Regina', needs_setup: true,
  billing: { status: 'trialing', trial_days_remaining: 30, checkout_available: true, checkout_defers_charge: true, customer_exists: false, subscription_exists: false },
}, userAgent = '', platform = '', maxTouchPoints = 0, search = '', failDeliveryOnce = false } = {}) {
  const nodes = new Map([
    ...['setup-delivery-channel', 'setup-delivery-summary', 'setup-paid-delivery', 'setup-pay-delivery', 'setup-discord-connection', 'setup-sms-connection', 'setup-whatsapp-connection'].map(id => [id, node()]),
    ['setup-status', node()],
    ['setup-content', node()],
    ['setup-continue', node({ textContent: 'Continue →' })],
    ['setup-skip', node()],
    ['setup-back', node()],
    ['setup-progress', node()],
    ['step-1', node({ hidden: false })],
    ['step-discord', node()],
    ['step-connect', node()],
    ['step-2', node()],
    ['step-message-categories', node()],
    ['step-message-windows', node()],
    ['step-task-create', node()],
    ['step-task-windows', node()],
    ['step-checkin-questions', node()],
    ['step-checkin-windows', node()],
    ['step-billing', node()],
    ['setup-billing-plan', node({value: 'discord'})],
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
    ['setup-billing-status', node()],
    ['setup-subscribe', node()],
    ['setup-billing-charge-heading', node()],
    ['setup-billing-charge-detail', node()],
    ['setup-billing-charge-hint', node()],
    ['setup-form', node()],
  ]);
  const requests = [];
  const navigation = [];
  const timers = [];
  let current = snapshot();
  const context = vm.createContext({
    document: {
      getElementById(id) { return nodes.get(id); },
      createElement() { return node(); },
      querySelectorAll() { return []; },
    },
    window: { dispatchEvent() {}, MHMSms: {mount(_parent, callback) {callback({eligible: false, connected: false, available: true});}}, MHMWhatsApp: {mount(_parent, callback) {callback({eligible: false, connected: false, available: true});}} },
    Event,
    URL,
    URLSearchParams,
    navigator: { userAgent, platform, maxTouchPoints },
    crypto: { randomUUID() { return String(Math.random()); } },
    history: { replaceState() {} },
    Intl: { DateTimeFormat() { return { resolvedOptions() { return { timeZone: 'America/Regina' }; } }; } },
    location: { search, pathname: '/setup.html', replace(url) { navigation.push(url); }, assign(url) { navigation.push(url); } },
    setTimeout(callback) { timers.push(callback); return timers.length; },
    fetch: async (url, options = {}) => {
      requests.push({ url, method: options.method || 'GET', body: options.body });
      if (url === '/api/account') return Response.json(account);
      if (url === '/api/settings' && options.method !== 'POST') return Response.json(current);
      if (url === '/api/settings') {
        const payload = JSON.parse(options.body);
        if (failDeliveryOnce && payload.section === 'delivery') {
          failDeliveryOnce = false;
          return Response.json({ error: 'Could not save delivery.' }, { status: 503 });
        }
        current = {
          ...current,
          sections: { ...current.sections, [payload.section]: payload.values },
          revisions: { ...current.revisions, [payload.section]: `${payload.section}-next` },
        };
        return Response.json(current);
      }
      if (url === '/api/tasks') return Response.json({ ok: true }, { status: 201 });
      if (url === '/api/account/setup-complete') return Response.json({ ok: true });
      if (url === '/api/auth/discord/start?next=/setup.html') return Response.json({ url: 'https://discord.com/oauth2/authorize?client_id=123&state=secure-state' });
      if (url === '/api/billing/checkout') return Response.json({ url: 'https://checkout.stripe.test/session' });
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
  }, async subscribe() {
    await nodes.get('setup-subscribe').listeners.click();
    for (let i = 0; i < 4; i += 1) await new Promise(resolve => setImmediate(resolve));
  }, async connectDiscord() {
    await nodes.get('setup-connect-discord').listeners.click();
    for (let i = 0; i < 4; i += 1) await new Promise(resolve => setImmediate(resolve));
  }, runTimers() {
    for (const callback of timers.splice(0)) callback();
  } };
}

test('Discord connection leaves setup usable if delivery settings fail to save', async () => {
  const view = await page({
    account: { needs_setup: true, discord_linked: true },
    search: '?discord=connected', failDeliveryOnce: true,
  });
  assert.equal(view.nodes.get('setup-content').hidden, false);
  assert.equal(view.nodes.get('step-connect').hidden, false);
  assert.match(view.nodes.get('setup-status').textContent, /Discord is connected.*could not confirm/);
  await view.continue();
  assert.equal(view.nodes.get('step-2').hidden, false);
});

test('first-run walks name, delivery, support choices, and a first task', async () => {
  const view = await page();
  assert.equal(view.nodes.get('setup-content').hidden, false);
  assert.equal(view.nodes.get('preferred-name').value, 'Brook');
  view.nodes.get('preferred-name').value = 'River';
  await view.continue();
  assert.equal(view.nodes.get('step-discord').hidden, false);
  await view.continue();
  assert.equal(view.nodes.get('step-2').hidden, false);
  const deliverySaves = view.requests
    .filter(request => request.url === '/api/settings' && request.method === 'POST')
    .map(request => JSON.parse(request.body))
    .filter(request => request.section === 'delivery');
  assert.equal(deliverySaves.at(-1).values.channel, 'email');
  view.nodes.get('enable-messages').checked = false;
  view.nodes.get('enable-checkins').checked = false;
  view.nodes.get('enable-tasks').checked = true;
  await view.continue();
  assert.equal(view.nodes.get('step-task-create').hidden, false);
  await view.continue();
  assert.equal(view.nodes.get('step-task-windows').hidden, false);
  await view.skip();
  assert.equal(view.nodes.get('step-billing').hidden, false);
  assert.match(view.nodes.get('setup-billing-status').textContent, /30 days remaining/);
  await view.continue();
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

test('billing is the final setup step and can open Stripe checkout immediately', async () => {
  const view = await page();
  await view.continue();
  await view.continue();
  view.nodes.get('enable-messages').checked = false;
  view.nodes.get('enable-tasks').checked = false;
  view.nodes.get('enable-checkins').checked = false;
  await view.continue();

  assert.equal(view.nodes.get('step-billing').hidden, false);
  assert.equal(view.nodes.get('setup-subscribe').hidden, false);
  assert.equal(view.nodes.get('setup-continue').textContent, 'Continue with free trial →');

  await view.subscribe();

  const posts = view.requests.filter(request => request.method === 'POST').map(request => request.url);
  assert.ok(posts.indexOf('/api/account/setup-complete') < posts.indexOf('/api/billing/checkout'));
  assert.deepEqual(view.navigation, ['https://checkout.stripe.test/session']);
});

test('near-expiry setup explains that subscribing charges immediately', async () => {
  const view = await page({
    account: {
      preferred_name: 'Brook', timezone: 'America/Regina', needs_setup: true,
      billing: { status: 'trialing', trial_days_remaining: 1, checkout_available: true, checkout_defers_charge: false, customer_exists: false, subscription_exists: false },
    },
  });
  await view.continue();
  await view.continue();
  view.nodes.get('enable-messages').checked = false;
  view.nodes.get('enable-tasks').checked = false;
  view.nodes.get('enable-checkins').checked = false;
  await view.continue();

  assert.equal(view.nodes.get('setup-billing-charge-heading').textContent, 'Billing starts when you subscribe');
  assert.match(view.nodes.get('setup-billing-charge-detail').textContent, /begins immediately/);
  assert.match(view.nodes.get('setup-billing-charge-hint').textContent, /charges the first payment for your selected plan/);
});

test('setup checkout sends the selected phone plan without a client-supplied price', async () => {
  const view = await page();
  view.nodes.get('setup-billing-plan').value = 'phone';
  await view.subscribe();
  const checkout = view.requests.find(request => request.url === '/api/billing/checkout');
  assert.deepEqual(JSON.parse(checkout.body), {plan: 'phone'});
});

test('Discord setup opens the Android app with a browser fallback', async () => {
  const view = await page({ userAgent: 'Mozilla/5.0 (Linux; Android 15; Pixel 9)' });
  await view.continue();
  await view.connectDiscord();

  assert.equal(view.navigation.length, 1);
  assert.match(view.navigation[0], /^intent:\/\/-\/oauth2\/authorize\?client_id=123&state=secure-state#Intent;/);
  assert.match(view.navigation[0], /scheme=discord;package=com\.discord;/);
  assert.match(view.navigation[0], /S\.browser_fallback_url=https%3A%2F%2Fdiscord\.com%2Foauth2%2Fauthorize/);
});

test('Discord setup opens the iOS app and falls back to the browser', async () => {
  const view = await page({ userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X)' });
  await view.continue();
  await view.connectDiscord();

  assert.deepEqual(view.navigation, ['discord://-/oauth2/authorize?client_id=123&state=secure-state']);
  view.runTimers();
  assert.deepEqual(view.navigation, [
    'discord://-/oauth2/authorize?client_id=123&state=secure-state',
    'https://discord.com/oauth2/authorize?client_id=123&state=secure-state',
  ]);
});

test('Discord setup keeps desktop authorization in the browser', async () => {
  const view = await page({ userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' });
  await view.continue();
  await view.connectDiscord();

  assert.deepEqual(view.navigation, ['https://discord.com/oauth2/authorize?client_id=123&state=secure-state']);
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

test('setup locks the active step while it is being saved', () => {
  assert.match(source, /const panel = current \? document\.getElementById\(current\.panel\) : null/);
  assert.match(source, /if \(panel\) setPanelEnabled\(panel, !busy\)/);
  assert.match(source, /setupForm\.setAttribute\('aria-busy', 'true'\)/);
  assert.match(source, /setupForm\.removeAttribute\('aria-busy'\)/);
});

test('delivery defaults to email and shows only the selected connection', async () => {
  const view = await page(); await view.continue();
  assert.match(view.nodes.get('setup-delivery-summary').textContent, /Selected: Email/);
  assert.equal(view.nodes.get('setup-discord-connection').hidden, true);
  assert.equal(view.nodes.get('setup-sms-connection').hidden, true);
  const choice = view.nodes.get('setup-delivery-channel');
  choice.value = 'whatsapp'; choice.listeners.change();
  assert.equal(view.nodes.get('step-connect').hidden, true);
  await view.continue();
  assert.equal(view.nodes.get('step-discord').hidden, true);
  assert.equal(view.nodes.get('step-connect').hidden, false);
  assert.equal(view.nodes.get('setup-whatsapp-connection').hidden, false);
  assert.equal(view.nodes.get('setup-paid-delivery').hidden, false);
  await view.continue();
  assert.equal(view.nodes.get('step-connect').hidden, false);
  assert.match(view.nodes.get('setup-status').textContent, /verify your phone/);
  await view.nodes.get('setup-pay-delivery').listeners.click();
  const checkout = view.requests.find(request => request.url === '/api/billing/checkout');
  assert.deepEqual(JSON.parse(checkout.body), {plan: 'whatsapp', setup_channel: 'whatsapp'});
  assert.equal(view.requests.some(request => request.url === '/api/account/setup-complete'), false);
});

test('checkout returns to the selected phone channel', async () => {
  const view = await page({search: '?setup_channel=sms&billing=success'});
  assert.equal(view.nodes.get('step-connect').hidden, false);
  assert.equal(view.nodes.get('setup-delivery-channel').value, 'sms');
  assert.equal(view.nodes.get('setup-sms-connection').hidden, false);
});

test('Discord connection is a subsequent step and Back returns to channel cards', async () => {
  const view = await page();
  await view.continue();
  const choice = view.nodes.get('setup-delivery-channel');
  choice.value = 'discord'; choice.listeners.change();
  assert.equal(view.nodes.get('step-connect').hidden, true);
  await view.continue();
  assert.equal(view.nodes.get('step-discord').hidden, true);
  assert.equal(view.nodes.get('step-connect').hidden, false);
  assert.equal(view.nodes.get('setup-discord-connection').hidden, false);
  assert.equal(view.requests.filter(request => request.url === '/api/settings' && request.method === 'POST').some(request => JSON.parse(request.body).values.channel === 'discord'), false);
  await view.nodes.get('setup-back').listeners.click();
  assert.equal(view.nodes.get('step-discord').hidden, false);
  assert.equal(choice.value, 'discord');
});
