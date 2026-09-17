import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';

const source = await readFile(new URL('./auth.js', import.meta.url), 'utf8');

test('account creation finishes without requiring Discord', async () => {
  const listeners = new Map();
  const nodes = new Map();
  const requests = [];
  const navigation = [];
  const document = {
    title: '',
    getElementById(id) {
      if (!nodes.has(id)) {
        nodes.set(id, {
          value: id === 'code' ? '123456' : id === 'password' ? 'a secure password phrase' : '',
          hidden: false,
          required: false,
          disabled: false,
          textContent: '',
          autocomplete: '',
          classList: { add() {}, remove() {}, toggle() {} },
          setAttribute() {},
          removeAttribute() {},
          focus() {},
          addEventListener(type, listener) { listeners.set(`${id}:${type}`, listener); },
        });
      }
      return nodes.get(id);
    },
    querySelectorAll() { return []; },
    querySelector() { return null; },
  };
  const context = vm.createContext({
    document,
    Intl,
    URLSearchParams,
    location: {
      search: '?mode=create',
      assign(url) { navigation.push(url); },
    },
    fetch: async (url) => {
      requests.push(url);
      if (url === '/api/auth/oauth/providers') return Response.json({ providers: {} });
      return Response.json({ ok: true });
    },
    Response,
    Error,
  });

  vm.runInContext(source, context);
  listeners.get('verify-form:submit')({ preventDefault() {} });
  await new Promise(resolve => setImmediate(resolve));
  await new Promise(resolve => setImmediate(resolve));

  assert.ok(requests.includes('/api/auth/verify'));
  assert.ok(!requests.includes('/api/auth/discord/start'));
  assert.deepEqual(navigation, ['app.html']);
});
