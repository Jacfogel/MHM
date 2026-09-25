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
  assert.equal((await worker.fetch(new Request(url + '/fonts/inter-latin.woff2'), env)).status, 200);
  assert.equal((await worker.fetch(new Request(url + '/fonts/nunito-latin.woff2'), env)).status, 200);
  assert.equal(await logo.text(), 'asset');
  assert.equal((await worker.fetch(new Request(url + '/tasks.js'), env)).status, 200);
  assert.equal((await worker.fetch(new Request(url + '/tasks.html'), env)).status, 200);
  assert.equal((await worker.fetch(new Request(url + '/notes.html'), env)).status, 200);
  assert.equal((await worker.fetch(new Request(url + '/notes.js'), env)).status, 200);
  assert.equal((await worker.fetch(new Request(url + '/checkin.html'), env)).status, 200);
  assert.equal((await worker.fetch(new Request(url + '/checkin.js'), env)).status, 200);
  assert.equal((await worker.fetch(new Request(url + '/insights.html'), env)).status, 200);
  assert.equal((await worker.fetch(new Request(url + '/insights.js'), env)).status, 200);
  assert.equal((await worker.fetch(new Request(url + '/messages.html'), env)).status, 200);
  assert.equal((await worker.fetch(new Request(url + '/messages.js'), env)).status, 200);
  assert.equal((await worker.fetch(new Request(url + '/home.html'), env)).status, 200);
  assert.equal((await worker.fetch(new Request(url + '/home.js'), env)).status, 200);
  assert.equal((await worker.fetch(new Request(url + '/setup.html'), env)).status, 200);
  assert.equal((await worker.fetch(new Request(url + '/setup.js'), env)).status, 200);
  assert.equal((await worker.fetch(new Request(url + '/privacy.html'), env)).status, 200);
  assert.equal((await worker.fetch(new Request(url + '/terms.html'), env)).status, 200);
  assert.equal((await worker.fetch(new Request(url + '/data.html'), env)).status, 200);
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

test('account self-service and insights routes proxy only their supported methods', async () => {
  const originalFetch = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (target, options) => {
    calls.push([target.href, options.method]);
    return Response.json({ ok: true });
  };
  try {
    const cookie = { Cookie: 'mhm_session=owned' };
    assert.equal((await worker.fetch(new Request(url + '/api/account/export', { headers: cookie }), env)).status, 200);
    assert.equal((await worker.fetch(new Request(url + '/api/insights?days=30', { headers: cookie }), env)).status, 200);
    assert.equal((await worker.fetch(new Request(url + '/api/health', { headers: cookie }), env)).status, 200);
    assert.equal((await worker.fetch(new Request(url + '/api/health', { method: 'POST', headers: { ...cookie, Origin: url, 'Content-Type': 'application/json' }, body: '{"action":"sync"}' }), env)).status, 200);
    assert.equal((await worker.fetch(new Request(url + '/api/account/connections', { method: 'POST', headers: { ...cookie, Origin: url, 'Content-Type': 'application/json' }, body: '{"provider":"google"}' }), env)).status, 200);
    assert.equal((await worker.fetch(new Request(url + '/api/account/setup-complete', { method: 'POST', headers: { ...cookie, Origin: url, 'Content-Type': 'application/json' }, body: '{}' }), env)).status, 200);
    assert.equal((await worker.fetch(new Request(url + '/api/account/delete', { method: 'POST', headers: { ...cookie, Origin: url, 'Content-Type': 'application/json' }, body: '{"confirmation":"DELETE"}' }), env)).status, 200);
    assert.equal((await worker.fetch(new Request(url + '/api/account/export', { method: 'POST', headers: { Origin: url } }), env)).status, 405);
    assert.deepEqual(calls, [
      ['https://gateway.example/api/account/export', 'GET'],
      ['https://gateway.example/api/insights?days=30', 'GET'],
      ['https://gateway.example/api/health', 'GET'],
      ['https://gateway.example/api/health', 'POST'],
      ['https://gateway.example/api/account/connections', 'POST'],
      ['https://gateway.example/api/account/setup-complete', 'POST'],
      ['https://gateway.example/api/account/delete', 'POST'],
    ]);
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
    assert.equal((await worker.fetch(new Request(url + '/api/tasks/task-1/snooze', {
      method: 'POST', headers: { Origin: url, Cookie: 'mhm_session=owned', 'Content-Type': 'application/json' }, body: '{"option":"1_hour"}',
    }), env)).status, 200);
    assert.deepEqual(calls.map(call => [call.href, call.method]), [
      [url.replace('https://mhm.example', 'https://gateway.example') + '/api/tasks/task-1', 'PATCH'],
      [url.replace('https://mhm.example', 'https://gateway.example') + '/api/tasks/task-1/complete', 'POST'],
      [url.replace('https://mhm.example', 'https://gateway.example') + '/api/tasks/task-1/snooze', 'POST'],
    ]);
    assert.equal(calls[0].body, '{"title":"Updated"}');
    assert.equal(calls[1].body, '{}');
    assert.equal(calls[2].body, '{"option":"1_hour"}');
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

test('message library routes preserve categories and allow bounded edits', async () => {
  const originalFetch = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (target, options) => { calls.push([target.href, options.method]); return Response.json({ message: { id: 'message-1' } }); };
  try {
    const headers = { Origin: url, Cookie: 'mhm_session=owned', 'Content-Type': 'application/json' };
    assert.equal((await worker.fetch(new Request(url + '/api/messages?category=motivational', { headers: { Cookie: 'mhm_session=owned' } }), env)).status, 200);
    assert.equal((await worker.fetch(new Request(url + '/api/messages/motivational/message-1', { method: 'PATCH', headers, body: '{"text":"Keep going","active":true,"days":["ALL"],"periods":["ALL"]}' }), env)).status, 200);
    assert.equal((await worker.fetch(new Request(url + '/api/messages/motivational/message-1', { method: 'DELETE', headers, body: '{}' }), env)).status, 200);
    assert.deepEqual(calls, [
      ['https://gateway.example/api/messages?category=motivational', 'GET'],
      ['https://gateway.example/api/messages/motivational/message-1', 'PATCH'],
      ['https://gateway.example/api/messages/motivational/message-1', 'DELETE'],
    ]);
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

test('website chat is proxied to the gateway', async () => {
  const originalFetch = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (target, options) => {
    calls.push({ href: target.href, method: options.method });
    return Response.json({ reply: 'Hi' });
  };
  try {
    assert.equal((await worker.fetch(new Request(url + '/api/chat', { headers: { Cookie: 'mhm_session=owned' } }), env)).status, 200);
    assert.equal((await worker.fetch(new Request(url + '/api/chat', {
      method: 'POST', headers: { Origin: url, 'Content-Type': 'application/json' }, body: '{"message":"hi"}',
    }), env)).status, 200);
    assert.deepEqual(calls.map(call => [call.href, call.method]), [
      ['https://gateway.example/api/chat', 'GET'],
      ['https://gateway.example/api/chat', 'POST'],
    ]);
  } finally { globalThis.fetch = originalFetch; }
});

test('check-in answers are proxied to the gateway', async () => {
  const originalFetch = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (target, options) => {
    calls.push({ href: target.href, method: options.method });
    return Response.json({ active: true });
  };
  try {
    assert.equal((await worker.fetch(new Request(url + '/api/checkins', { headers: { Cookie: 'mhm_session=owned' } }), env)).status, 200);
    assert.equal((await worker.fetch(new Request(url + '/api/checkins', {
      method: 'POST', headers: { Origin: url, 'Content-Type': 'application/json' }, body: '{"action":"start"}',
    }), env)).status, 200);
    assert.deepEqual(calls.map(call => [call.href, call.method]), [
      ['https://gateway.example/api/checkins', 'GET'],
      ['https://gateway.example/api/checkins', 'POST'],
    ]);
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

test('password and social auth routes proxy and Apple callbacks stay closed', async () => {
  const originalFetch = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (target, options) => {
    calls.push({ href: target.href, method: options.method });
    if (target.pathname.endsWith('/callback')) {
      return new Response(null, { status: 302, headers: { Location: url + '/home.html?social=google-connected' } });
    }
    return Response.json({ ok: true, url: 'https://provider.example/authorize' });
  };
  try {
    assert.equal((await worker.fetch(post('/api/auth/password'), env)).status, 200);
    assert.equal((await worker.fetch(new Request(url + '/api/auth/oauth/google/start'), env)).status, 200);
    const callback = await worker.fetch(new Request(url + '/api/auth/oauth/google/callback?code=abc&state=xyz'), env);
    assert.equal(callback.status, 302);
    assert.equal(callback.headers.get('Location'), url + '/home.html?social=google-connected');
    assert.equal((await worker.fetch(new Request(url + '/api/auth/oauth/apple/callback', {
      method: 'POST',
      headers: { Origin: url, 'Content-Type': 'application/json' },
      body: '{}',
    }), env)).status, 404);
    assert.deepEqual(calls.map(call => [call.href, call.method]), [
      ['https://gateway.example/api/auth/password', 'POST'],
      ['https://gateway.example/api/auth/oauth/google/start', 'GET'],
      ['https://gateway.example/api/auth/oauth/google/callback?code=abc&state=xyz', 'GET'],
    ]);
  } finally { globalThis.fetch = originalFetch; }
});
