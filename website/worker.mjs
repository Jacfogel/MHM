const routes = new Map([
  ['/api/auth/request-code', 'POST'], ['/api/auth/verify', 'POST'],
  ['/api/auth/logout', 'POST'], ['/api/account', 'GET'],
  ['/api/auth/discord/start', 'GET'], ['/api/auth/discord/callback', 'GET'],
  ['/api/settings', ['GET', 'POST']],
]);
const assets = new Set(['/', '/index.html', '/login', '/login.html', '/app', '/app.html', '/styles.css', '/script.js', '/auth.js', '/app.js', '/settings.js']);
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
    const methods = routes.get(url.pathname);
    if (!methods) return error('Page not found.', 404);
    const method = request.method;
    if (!(Array.isArray(methods) ? methods : [methods]).includes(method)) return error('This method is not supported.', 405);
    if (method === 'POST' && request.headers.get('Origin') !== url.origin) {
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
      if (method === 'POST' && request.body) {
        const reader = request.body.getReader();
        const chunks = [];
        let size = 0;
        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          size += value.byteLength;
          if (size > (url.pathname === '/api/settings' ? 32768 : 4096)) {
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
        redirect: url.pathname === '/api/auth/discord/callback' ? 'manual' : 'error',
        signal: AbortSignal.timeout(15000),
      });
      return secured(response, true);
    } catch {
      return error('MHM could not connect. Please try again shortly.', 503);
    }
  },
};
