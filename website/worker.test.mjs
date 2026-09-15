import test from 'node:test';
import assert from 'node:assert/strict';
import worker from './worker.mjs';

const url = 'https://mhm.example';
const env = { MHM_API_ORIGIN: 'https://gateway.example', MHM_API_SECRET: 's'.repeat(32), ASSETS: { fetch: async () => new Response('asset') } };
function post(path = '/api/auth/request-code', origin = url) {
  return new Request(url + path, { method: 'POST', headers: { Origin: origin, 'Content-Type': 'application/json', 'CF-Connecting-IP': '192.0.2.1', 'X-MHM-Proxy-Secret': 'forged' }, body: '{}' });
}

test('static pages get security headers and internal files stay private', async () => {
  const response = await worker.fetch(new Request(url + '/login.html'), env);
  assert.equal(await response.text(), 'asset');
  assert.match(response.headers.get('Content-Security-Policy'), /frame-ancestors 'none'/);
  assert.equal((await worker.fetch(new Request(url + '/worker.mjs'), env)).status, 404);
  const logo = await worker.fetch(new Request(url + '/mhm-logo.png'), env);
  assert.equal(logo.status, 200);
  assert.equal(await logo.text(), 'asset');
  assert.equal((await worker.fetch(new Request(url + '/tasks.js'), env)).status, 200);
  assert.equal((await worker.fetch(new Request(url + '/tasks.html'), env)).status, 200);
  assert.equal((await worker.fetch(new Request(url + '/notes.html'), env)).status, 200);
  assert.equal((await worker.fetch(new Request(url + '/notes.js'), env)).status, 200);
  assert.equal((await worker.fetch(new Request(url + '/other-image.png'), env)).status, 404);
});
test('missing configuration, cross-origin submissions and unknown routes fail closed', async () => {
  assert.equal((await worker.fetch(post(), {})).status, 503);
  assert.equal((await worker.fetch(post(undefined, 'https://other.example'), env)).status, 403);
  assert.equal((await worker.fetch(post('/api/admin'), env)).status, 404);
  assert.equal((await worker.fetch(new Request(url + '/api/account', { method: 'DELETE' }), env)).status, 405);
});
test('proxy forwards authenticated address, body, cookies and response cookie', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (target, options) => {
    assert.equal(target.href, 'https://gateway.example/api/auth/request-code');
    assert.equal(options.headers.get('X-MHM-Proxy-Secret'), env.MHM_API_SECRET);
    assert.equal(options.headers.get('X-MHM-Client-IP'), '192.0.2.1');
    assert.equal(options.headers.get('Origin'), url);
    assert.equal(new TextDecoder().decode(options.body), '{}');
    assert.equal(options.redirect, 'manual');
    return Response.json({ ok: true }, { headers: { 'Set-Cookie': 'mhm_session=test; HttpOnly; Secure' } });
  };
  try {
    const response = await worker.fetch(post(), env);
    assert.equal(response.status, 200);
    assert.equal(response.headers.get('Cache-Control'), 'no-store');
    assert.match(response.headers.get('Set-Cookie'), /HttpOnly/);
  } finally { globalThis.fetch = originalFetch; }
});
test('unreachable and invalid origins show a recoverable error', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => { throw new Error('unreachable'); };
  try {
    assert.equal((await worker.fetch(post(), env)).status, 503);
    assert.equal((await worker.fetch(post(), { ...env, MHM_API_ORIGIN: 'http://gateway.example' })).status, 503);
    assert.equal((await worker.fetch(post(), { ...env, MHM_API_ORIGIN: url })).status, 503);
  } finally { globalThis.fetch = originalFetch; }
});
test('oversized bodies are rejected before proxying', async () => {
  const request = new Request(url + '/api/auth/request-code', {
    method: 'POST', headers: { Origin: url, 'Content-Type': 'application/json' }, body: 'x'.repeat(4097),
  });
  assert.equal((await worker.fetch(request, env)).status, 413);
});

test('unexpected gateway redirects are blocked without following or exposing their destination', async () => {
  const originalFetch = globalThis.fetch;
  let calls = 0;
  globalThis.fetch = async (_target, options) => {
    calls++;
    assert.equal(options.redirect, 'manual');
    return new Response('redirect body', { status: 302, headers: { Location: 'https://other.example/private' } });
  };
  try {
    const response = await worker.fetch(post(), env);
    assert.equal(response.status, 503);
    assert.equal(response.headers.get('Location'), null);
    assert.equal(calls, 1);
  } finally { globalThis.fetch = originalFetch; }
});

test('settings allow authenticated reads and bounded saves through the proxy', async () => {
  const originalFetch = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (target, options) => {
    assert.equal(target.href, 'https://gateway.example/api/settings');
    assert.equal(options.headers.get('Cookie'), 'mhm_session=owned');
    calls.push(options.method);
    return Response.json({ sections: {} });
  };
  try {
    assert.equal((await worker.fetch(new Request(url + '/api/settings', { headers: { Cookie: 'mhm_session=owned' } }), env)).status, 200);
    assert.equal((await worker.fetch(new Request(url + '/api/settings', { method: 'POST', headers: { Origin: url, Cookie: 'mhm_session=owned', 'Content-Type': 'application/json' }, body: JSON.stringify({ values: 'x'.repeat(5000) }) }), env)).status, 200);
    assert.deepEqual(calls, ['GET', 'POST']);
    assert.equal((await worker.fetch(new Request(url + '/api/settings', { method: 'POST', headers: { Origin: url, 'Content-Type': 'application/json' }, body: 'x'.repeat(32769) }), env)).status, 413);
    assert.equal((await worker.fetch(new Request(url + '/api/settings', { method: 'DELETE' }), env)).status, 405);
  } finally { globalThis.fetch = originalFetch; }
});

test('task CRUD routes forward dynamic IDs and mutating methods safely', async () => {
  const originalFetch = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (target, options) => {
    calls.push({ href: target.href, method: options.method, body: new TextDecoder().decode(options.body) });
    return Response.json({ task: { id: 'task-1' } });
  };
  try {
    const patch = new Request(url + '/api/tasks/task-1', {
      method: 'PATCH', headers: { Origin: url, Cookie: 'mhm_session=owned', 'Content-Type': 'application/json' }, body: '{"title":"Updated"}',
    });
    assert.equal((await worker.fetch(patch, env)).status, 200);
    assert.equal((await worker.fetch(new Request(url + '/api/tasks/task-1/complete', {
      method: 'POST', headers: { Origin: url, Cookie: 'mhm_session=owned', 'Content-Type': 'application/json' }, body: '{}',
    }), env)).status, 200);
    assert.deepEqual(calls.map(call => [call.href, call.method]), [
      [url.replace('https://mhm.example', 'https://gateway.example') + '/api/tasks/task-1', 'PATCH'],
      [url.replace('https://mhm.example', 'https://gateway.example') + '/api/tasks/task-1/complete', 'POST'],
    ]);
    assert.equal(calls[0].body, '{"title":"Updated"}');
    assert.equal(calls[1].body, '{}');
  } finally { globalThis.fetch = originalFetch; }
});

test('notes routes forward dynamic IDs and archive actions', async () => {
  const originalFetch = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (target, options) => { calls.push({ href: target.href, method: options.method, body: new TextDecoder().decode(options.body) }); return Response.json({ note: { id: 'note-1' } }); };
  try {
    assert.equal((await worker.fetch(new Request(url + '/api/notes/note-1', { method: 'PATCH', headers: { Origin: url, Cookie: 'mhm_session=owned', 'Content-Type': 'application/json' }, body: '{"description":"Updated"}' }), env)).status, 200);
    assert.equal((await worker.fetch(new Request(url + '/api/notes/note-1/archive', { method: 'POST', headers: { Origin: url, Cookie: 'mhm_session=owned', 'Content-Type': 'application/json' }, body: '{}' }), env)).status, 200);
    assert.deepEqual(calls.map(call => [call.href, call.method]), [[url.replace('https://mhm.example', 'https://gateway.example') + '/api/notes/note-1', 'PATCH'], [url.replace('https://mhm.example', 'https://gateway.example') + '/api/notes/note-1/archive', 'POST']]);
    assert.equal(calls[0].body, '{"description":"Updated"}');
  } finally { globalThis.fetch = originalFetch; }
});

test('notes queries survive proxying and unsupported mutations stay blocked', async () => {
  const originalFetch = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (target, options) => {
    calls.push({ href: target.href, method: options.method });
    return Response.json({ notes: [] });
  };
  try {
    const query = new Request(url + '/api/notes?status=archived&q=steady', { headers: { Cookie: 'mhm_session=owned' } });
    assert.equal((await worker.fetch(query, env)).status, 200);
    assert.deepEqual(calls, [{ href: 'https://gateway.example/api/notes?status=archived&q=steady', method: 'GET' }]);
    assert.equal((await worker.fetch(new Request(url + '/api/notes/note-1', { method: 'DELETE' }), env)).status, 405);
    assert.equal((await worker.fetch(new Request(url + '/api/notes/note-1/publish', { method: 'POST', headers: { Origin: url } }), env)).status, 404);
    assert.equal(calls.length, 1);
  } finally { globalThis.fetch = originalFetch; }
});

test('oversized notebook writes are rejected before reaching the gateway', async () => {
  const originalFetch = globalThis.fetch;
  let proxied = false;
  globalThis.fetch = async () => { proxied = true; return Response.json({}); };
  try {
    const request = new Request(url + '/api/notes', {
      method: 'POST',
      headers: { Origin: url, 'Content-Type': 'application/json' },
      body: 'x'.repeat(65537),
    });
    assert.equal((await worker.fetch(request, env)).status, 413);
    assert.equal(proxied, false);
  } finally { globalThis.fetch = originalFetch; }
});

test('Discord callback keeps its query and returns the gateway redirect', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (target, options) => {
    assert.equal(target.href, 'https://gateway.example/api/auth/discord/callback?code=abc&state=xyz');
    assert.equal(options.redirect, 'manual');
    assert.equal(options.headers.get('Cookie'), 'mhm_session=owned');
    return new Response(null, { status: 302, headers: { Location: url + '/app.html?discord=connected' } });
  };
  try {
    const response = await worker.fetch(new Request(url + '/api/auth/discord/callback?code=abc&state=xyz', { headers: { Cookie: 'mhm_session=owned' } }), env);
    assert.equal(response.status, 302);
    assert.equal(response.headers.get('Location'), url + '/app.html?discord=connected');
  } finally { globalThis.fetch = originalFetch; }
});
