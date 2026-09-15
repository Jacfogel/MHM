const creating = new URLSearchParams(location.search).get('mode') === 'create';
const socialResult = new URLSearchParams(location.search).get('social');
const status = document.getElementById('auth-status');
const entry = document.getElementById('entry-step');
const verification = document.getElementById('verify-step');
const password = document.getElementById('password');
let challenge = '';
let busy = false;

if (creating) {
  document.title = 'Create your account — MHM';
  document.getElementById('login-tab').removeAttribute('aria-current');
  document.getElementById('create-tab').setAttribute('aria-current', 'page');
  document.getElementById('create-fields').hidden = false;
  document.getElementById('username').required = true;
  document.getElementById('confirm-password-field').hidden = false;
  document.getElementById('confirm-password').required = true;
  password.autocomplete = 'new-password';
  document.getElementById('form-title').textContent = 'Start where you are.';
  document.getElementById('form-description').textContent = 'Create your MHM account with a password. We’ll verify your email once before getting you started.';
  document.getElementById('email-hint').textContent = 'We’ll send your one-time verification code here.';
  document.getElementById('primary-action').textContent = 'Create my account →';
  document.getElementById('send-code').hidden = true;
}

const socialMessages = {
  cancelled: 'Social sign-in was canceled. You can try again whenever you are ready.',
  unavailable: 'That sign-in provider is not available right now.',
  'not-linked': 'No active MHM account matches that social account. Create an account or use your account email first.',
  expired: 'That sign-in attempt expired. Please start again.',
  'in-use': 'That social account is already connected to another MHM account.',
  error: 'Social sign-in could not be completed. Please try again.',
};
if (socialResult && socialMessages[socialResult]) {
  status.textContent = socialMessages[socialResult];
  status.classList.toggle('is-error', socialResult !== 'cancelled');
}

async function api(path, data) {
  const response = await fetch(path, {
    method: data === undefined ? 'GET' : 'POST', credentials: 'same-origin', cache: 'no-store',
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

function accountValues() {
  return {
    email: document.getElementById('email').value.trim(),
    password: password.value,
    username: document.getElementById('username').value.trim(),
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'America/Regina',
  };
}

async function requestEmailCode(values) {
  const result = await api('/api/auth/request-code', {
    mode: creating ? 'create' : 'login', email: values.email,
    username: values.username, timezone: values.timezone,
  });
  challenge = result.challenge;
  entry.hidden = true;
  verification.hidden = false;
  document.getElementById('code-description').textContent = creating
    ? `Look for a code at ${values.email}. Your password is saved only after this verification succeeds.`
    : `Look for a code at ${values.email}. Codes are sent to the email saved on your MHM account.`;
  status.textContent = '';
  document.getElementById('code').focus();
}

document.getElementById('account-form').addEventListener('submit', (event) => {
  event.preventDefault();
  const values = accountValues();
  const button = document.getElementById('primary-action');
  submit(button, async () => {
    if (creating) {
      if (password.value !== document.getElementById('confirm-password').value) {
        throw new Error('Those passwords do not match.');
      }
      await requestEmailCode(values);
      return;
    }
    await api('/api/auth/password', { email: values.email, password: values.password });
    location.assign('app.html');
  });
});

document.getElementById('send-code').addEventListener('click', () => {
  const values = accountValues();
  if (!document.getElementById('email').checkValidity()) {
    document.getElementById('email').reportValidity();
    return;
  }
  submit(document.getElementById('send-code'), () => requestEmailCode(values));
});

document.getElementById('verify-form').addEventListener('submit', (event) => {
  event.preventDefault();
  submit(document.getElementById('verify-code'), async () => {
    const payload = { challenge, code: document.getElementById('code').value.trim() };
    if (creating) payload.password = password.value;
    await api('/api/auth/verify', payload);
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

async function loadSocialProviders() {
  try {
    const result = await api('/api/auth/oauth/providers');
    const available = Object.entries(result.providers || {}).filter(([, enabled]) => enabled);
    for (const [provider] of available) {
      const button = document.querySelector(`[data-provider="${provider}"]`);
      if (button) button.disabled = false;
    }
    document.getElementById('social-hint').textContent = available.length
      ? 'Use a connected provider, or continue with email.'
      : 'Social sign-in is being set up. Use email for now.';
  } catch (_) {
    document.getElementById('social-hint').textContent = 'Social sign-in is unavailable right now. Use email instead.';
  }
}

for (const button of document.querySelectorAll('[data-provider]')) {
  button.addEventListener('click', () => submit(button, async () => {
    const provider = button.dataset.provider;
    const result = await api(`/api/auth/oauth/${provider}/start`);
    if (!result.url) throw new Error(`${provider} sign-in is unavailable.`);
    location.assign(result.url);
  }));
}
loadSocialProviders();
