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
    assert.deepEqual(navigation, ['setup.html']);
});

test('password recovery verifies the email code before sending the new password', async () => {
  const listeners = new Map();
  const nodes = new Map();
  const requests = [];
  const navigation = [];
  const values = {
    email: 'river@example.com',
    password: 'a newly recovered password',
    'confirm-password': 'a newly recovered password',
    code: '654321',
  };
  const document = {
    title: '',
    getElementById(id) {
      if (!nodes.has(id)) {
        nodes.set(id, {
          value: values[id] || '',
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
      search: '?mode=reset',
      assign(url) { navigation.push(url); },
    },
    fetch: async (url, options = {}) => {
      requests.push({ url, payload: options.body ? JSON.parse(options.body) : null });
      if (url === '/api/auth/request-code') return Response.json({ challenge: 'reset-token' });
      if (url === '/api/auth/oauth/providers') return Response.json({ providers: {} });
      return Response.json({ ok: true });
    },
    Response,
    Error,
  });

  vm.runInContext(source, context);
  listeners.get('account-form:submit')({ preventDefault() {} });
  await new Promise(resolve => setImmediate(resolve));
  listeners.get('verify-form:submit')({ preventDefault() {} });
  await new Promise(resolve => setImmediate(resolve));
  await new Promise(resolve => setImmediate(resolve));

  const codeRequest = requests.find(request => request.url === '/api/auth/request-code');
  const verification = requests.find(request => request.url === '/api/auth/verify');
  assert.equal(codeRequest.payload.mode, 'reset');
  assert.deepEqual(verification.payload, {
    challenge: 'reset-token',
    code: '654321',
    password: 'a newly recovered password',
  });
    assert.deepEqual(navigation, ['home.html']);
});
