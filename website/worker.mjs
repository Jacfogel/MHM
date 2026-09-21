const routes = new Map([
  ['/api/auth/request-code', 'POST'], ['/api/auth/verify', 'POST'],
  ['/api/auth/password', 'POST'], ['/api/auth/password/setup', 'POST'],
  ['/api/auth/logout', 'POST'], ['/api/account', 'GET'],
  ['/api/account/connections', 'POST'], ['/api/account/export', 'GET'],
  ['/api/auth/oauth/providers', 'GET'],
  ['/api/auth/discord/start', 'GET'], ['/api/auth/discord/callback', 'GET'],
  ['/api/settings', ['GET', 'POST']],
  ['/api/insights', 'GET'],
  ['/api/health', ['GET', 'POST']],
  ['/api/task-templates', 'GET'],
  ['/api/tasks', ['GET', 'POST']],
  ['/api/actions', 'POST'],
  ['/api/messages', ['GET', 'POST']],
  ['/api/notes', ['GET', 'POST']],
]);
const assets = new Set(['/', '/index.html', '/login', '/login.html', '/home', '/home.html', '/setup', '/setup.html', '/app', '/app.html', '/tasks', '/tasks.html', '/notes', '/notes.html', '/insights', '/insights.html', '/messages', '/messages.html', '/styles.css', '/script.js', '/auth.js', '/app.js', '/home.js', '/setup.js', '/settings.js', '/tasks.js', '/notes.js', '/insights.js', '/messages.js', '/mhm-logo.png']);
const csp = "default-src 'self'; style-src 'self' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'";

function secured(response, api = false) {
  const result = new Response(response.body, response);
  result.headers.set('X-Content-Type-Options', 'nosniff');
  result.headers.set('Referrer-Policy', 'same-origin');
  result.headers.set('Content-Security-Policy', csp);
  if (api) result.headers.set('Cache-Control', 'no-store');
  return result;
}
function error(message, status) {
  return secured(Response.json({ error: message }, { status }), true);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (!url.pathname.startsWith('/api/')) {
      if (!assets.has(url.pathname)) return secured(new Response('Page not found.', { status: 404 }));
      return secured(await env.ASSETS.fetch(request));
    }
    const taskAction = url.pathname.match(/^\/api\/tasks\/[^/]+(?:\/(?:complete|restore|snooze|skip|simplify))?$/);
    const noteAction = url.pathname.match(/^\/api\/notes\/[^/]+(?:\/(?:archive|restore))?$/);
    const messageAction = url.pathname.match(/^\/api\/messages\/[^/]+\/[^/]+$/);
    const oauthStart = url.pathname.match(/^\/api\/auth\/oauth\/(?:google|facebook|apple)\/start$/);
    const oauthCallback = url.pathname.match(/^\/api\/auth\/oauth\/(?:google|facebook|apple)\/callback$/);
    const routePath = taskAction || noteAction || messageAction || oauthStart || oauthCallback
      ? taskAction ? '/api/tasks/:task_id' : noteAction ? '/api/notes/:note_id' : messageAction ? '/api/messages/:category/:message_id' : oauthStart ? '/api/auth/oauth/:provider/start' : '/api/auth/oauth/:provider/callback'
      : url.pathname;
    const methods = oauthStart ? ['GET']
      : oauthCallback ? (url.pathname.includes('/apple/') ? ['GET', 'POST'] : ['GET'])
      : taskAction
      ? (/\/(?:complete|restore|snooze|skip|simplify)$/.test(url.pathname) ? ['POST'] : ['PATCH', 'DELETE'])
      : noteAction
        ? (url.pathname.endsWith('/archive') || url.pathname.endsWith('/restore') ? ['POST'] : ['PATCH'])
      : messageAction ? ['PATCH', 'DELETE']
      : routes.get(routePath);
    if (!methods) return error('Page not found.', 404);
    const method = request.method;
    if (!(Array.isArray(methods) ? methods : [methods]).includes(method)) return error('This method is not supported.', 405);
    const appleCallback = url.pathname === '/api/auth/oauth/apple/callback' && method === 'POST';
    if (method !== 'GET' && !appleCallback && request.headers.get('Origin') !== url.origin) {
      return error('Please sign in through the MHM website.', 403);
    }
    if (!env.MHM_API_ORIGIN || !env.MHM_API_SECRET || env.MHM_API_SECRET.length < 32) {
      return error('Email sign-in is not available yet. Please try again later.', 503);
    }
    try {
      const origin = new URL(env.MHM_API_ORIGIN);
      if (origin.protocol !== 'https:' || origin.pathname !== '/' || origin.username || origin.password || origin.search || origin.hash || origin.origin === url.origin) {
        return error('Email sign-in is not available yet. Please try again later.', 503);
      }
      const headers = new Headers();
      for (const name of ['Content-Type', 'Cookie', 'Origin']) {
        const value = request.headers.get(name);
        if (value) headers.set(name, value);
      }
      headers.set('X-MHM-Proxy-Secret', env.MHM_API_SECRET);
      headers.set('X-MHM-Client-IP', request.headers.get('CF-Connecting-IP') || 'unknown');
      let body;
      if (method !== 'GET' && request.body) {
        const reader = request.body.getReader();
        const chunks = [];
        let size = 0;
        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          size += value.byteLength;
          const maxBody = url.pathname === '/api/settings' ? 32768 : url.pathname.startsWith('/api/tasks') ? 8192 : url.pathname.startsWith('/api/notes') ? 65536 : 4096;
          if (size > maxBody) {
            await reader.cancel();
            return error('This request is too large.', 413);
          }
          chunks.push(value);
        }
        body = new Uint8Array(size);
        let offset = 0;
        for (const chunk of chunks) { body.set(chunk, offset); offset += chunk.byteLength; }
      }
      const response = await fetch(new URL(url.pathname + url.search, origin), {
        method, headers, body,
        // Workers supports only follow/manual. Never follow a gateway redirect:
        // it could forward the proxy secret and session cookie to another host.
        redirect: 'manual',
        signal: AbortSignal.timeout(15000),
      });
      if (response.status >= 300 && response.status < 400 && url.pathname !== '/api/auth/discord/callback' && !oauthCallback) {
        if (response.body) await response.body.cancel();
        return error('MHM could not connect. Please try again shortly.', 503);
      }
      return secured(response, true);
    } catch {
      return error('MHM could not connect. Please try again shortly.', 503);
    }
  },
};
