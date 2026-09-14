const creating = new URLSearchParams(location.search).get('mode') === 'create';
const status = document.getElementById('auth-status');
const entry = document.getElementById('entry-step');
const verification = document.getElementById('verify-step');
let challenge = '';
let busy = false;

if (creating) {
  document.title = 'Create your account — MHM';
  document.getElementById('login-tab').removeAttribute('aria-current');
  document.getElementById('create-tab').setAttribute('aria-current', 'page');
  document.getElementById('create-fields').hidden = false;
  document.getElementById('username').required = true;
  document.getElementById('form-title').textContent = 'Start where you are.';
  document.getElementById('form-description').textContent = "Create your MHM account. We'll verify your email before getting you started.";
  document.getElementById('email-hint').textContent = 'We’ll send your verification code here.';
  document.getElementById('send-code').textContent = 'Create my account →';
}

async function api(path, data) {
  const response = await fetch(path, {
    method: data === undefined ? 'GET' : 'POST', credentials: 'same-origin',
    headers: data === undefined ? {} : { 'Content-Type': 'application/json' },
    body: data === undefined ? undefined : JSON.stringify(data),
  });
  const result = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(result.error || 'MHM could not connect. Please try again shortly.');
  return result;
}

async function submit(button, operation) {
  if (busy) return;
  busy = true;
  button.disabled = true;
  button.setAttribute('aria-busy', 'true');
  status.textContent = 'Connecting…';
  status.classList.remove('is-error');
  try { await operation(); }
  catch (error) { status.textContent = error.message; status.classList.add('is-error'); }
  finally { busy = false; button.disabled = false; button.removeAttribute('aria-busy'); }
}

document.getElementById('account-form').addEventListener('submit', (event) => {
  event.preventDefault();
  submit(document.getElementById('send-code'), async () => {
    const email = document.getElementById('email').value.trim();
    const result = await api('/api/auth/request-code', {
      mode: creating ? 'create' : 'login', email,
      username: document.getElementById('username').value.trim(),
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'America/Regina',
    });
    challenge = result.challenge;
    entry.hidden = true;
    verification.hidden = false;
    document.getElementById('code-description').textContent = creating
      ? `Look for a code at ${email}. Already have an account? Choose Log in to continue.`
      : `Look for a code at ${email}. Codes are sent to the email saved on your MHM account.`;
    status.textContent = '';
    document.getElementById('code').focus();
  });
});

document.getElementById('verify-form').addEventListener('submit', (event) => {
  event.preventDefault();
  submit(document.getElementById('verify-code'), async () => {
    await api('/api/auth/verify', { challenge, code: document.getElementById('code').value.trim() });
    if (creating) {
      try {
        const connection = await api('/api/auth/discord/start');
        if (connection.url) { location.assign(connection.url); return; }
      } catch (_) {
        // Account creation still succeeds when Discord OAuth is not configured.
      }
    }
    location.assign('app.html');
  });
});

document.getElementById('start-over').addEventListener('click', () => {
  if (busy) return;
  challenge = '';
  verification.hidden = true;
  entry.hidden = false;
  document.getElementById('code').value = '';
  status.textContent = '';
  document.getElementById('email').focus();
});
