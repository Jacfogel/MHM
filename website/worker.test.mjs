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
    assert.equal(options.redirect, 'error');
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
