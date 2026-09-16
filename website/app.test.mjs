import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';

const source = await readFile(new URL('./app.js', import.meta.url), 'utf8');
const profile = { preferred_name: 'Test', email: 'test@example.com', timezone: 'America/Regina' };

async function page(logoutFetch = async () => Response.json({ ok: true })) {
  let click;
  const nodes = new Map();
  const document = {
    getElementById(id) {
      if (!nodes.has(id)) nodes.set(id, { hidden: true, disabled: false, textContent: '', classList: { add() {}, remove() {} }, replaceChildren() {}, addEventListener(type, listener) { if (id === 'logout' && type === 'click') click = listener; } });
      return nodes.get(id);
    },
  };
  const window = new EventTarget();
  const requests = [];
  const navigation = [];
  const context = vm.createContext({ document, window, Event, AbortSignal, URLSearchParams, location: { search: '', replace(url) { navigation.push(url); } }, fetch: async (url, options) => {
    requests.push(url);
    return url === '/api/account' ? Response.json(profile) : logoutFetch(url, options);
  } });
  vm.runInContext(source, context);
  await new Promise(resolve => setImmediate(resolve));
  return { nodes, window, requests, navigation, async logout() {
    const event = { currentTarget: document.getElementById('logout') };
    const pending = click(event);
    // Browser events clear currentTarget after synchronous event dispatch.
    event.currentTarget = null;
    await pending;
  } };
}

test('canceling unsaved-change confirmation leaves the session and page intact', async () => {
  const view = await page();
  view.window.addEventListener('mhm:before-logout', event => event.preventDefault());
  await view.logout();
  assert.deepEqual(view.requests, ['/api/account']);
  assert.deepEqual(view.navigation, []);
  assert.equal(view.nodes.get('account-content').hidden, false);
  assert.equal(view.nodes.get('logout').disabled, false);
});

test('successful logout releases the navigation guard and hides account data before leaving', async () => {
  const view = await page(async (url, options) => {
    assert.equal(options.method, 'POST');
    assert.equal(options.credentials, 'same-origin');
    return Response.json({ ok: true });
  });
  let released = false;
  view.window.addEventListener('mhm:signed-out', () => { released = true; });
  await view.logout();
  assert.equal(released, true);
  assert.equal(view.nodes.get('account-content').hidden, true);
  assert.deepEqual(view.navigation, ['login.html']);
});

test('a failed request re-enables the button after the browser clears currentTarget', async () => {
  let attempts = 0;
  const view = await page(async () => {
    if (++attempts === 1) throw new Error('offline');
    return Response.json({ ok: true });
  });
  await view.logout();
  assert.equal(view.nodes.get('logout').disabled, false);
  assert.match(view.nodes.get('app-status').textContent, /Please try again/);
  assert.equal(view.nodes.get('account-content').hidden, false);
  await view.logout();
  assert.deepEqual(view.navigation, ['login.html']);
});

test('an expired session also clears account data and returns to login', async () => {
  const view = await page(async () => Response.json({}, { status: 401 }));
  await view.logout();
  assert.equal(view.nodes.get('account-content').hidden, true);
  assert.deepEqual(view.navigation, ['login.html']);
});
