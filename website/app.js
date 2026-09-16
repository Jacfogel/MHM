const status = document.getElementById('app-status');
const accountContent = document.getElementById('account-content');
let accountSessionEnded = false;
const discordResult = new URLSearchParams(location.search).get('discord');
const socialResult = new URLSearchParams(location.search).get('social');
window.addEventListener('mhm:signed-out', () => {
  accountSessionEnded = true;
  if (accountContent) accountContent.hidden = true;
});
function returnToLogin() {
  window.dispatchEvent(new Event('mhm:signed-out'));
  if (accountContent) accountContent.hidden = true;
  location.replace('login.html');
}
async function loadAccount() {
  if (!accountContent) return;
  try {
    const response = await fetch('/api/account', { credentials: 'same-origin', cache: 'no-store' });
    if (response.status === 401) { returnToLogin(); return; }
    if (!response.ok) throw new Error('Your account could not load. Please refresh to try again.');
    const account = await response.json();
    if (accountSessionEnded) return;
    document.getElementById('account-name').textContent = account.preferred_name || 'there';
    document.getElementById('account-email').textContent = account.email;
    document.getElementById('account-timezone').textContent = account.timezone || 'Not set';
    document.getElementById('account-discord').textContent = account.discord_linked ? 'Connected' : 'Not connected yet';
    document.getElementById('password-heading').textContent = account.password_set ? 'Change your password.' : 'Set a password.';
    document.getElementById('password-guidance').textContent = account.password_set
      ? 'Your password is set. You can replace it here whenever you need to.'
      : 'Add a password so your next sign-in does not need an emailed code.';
    document.getElementById('current-password-field').hidden = !account.password_change_requires_current;
    document.getElementById('current-password').required = account.password_change_requires_current;
    const socialConnections = document.getElementById('social-connections');
    socialConnections.replaceChildren();
    let socialCount = 0;
    for (const [provider, details] of Object.entries(account.oauth || {})) {
      if (!details.available && !details.linked) continue;
      socialCount += 1;
      const row = document.createElement('div');
      row.className = 'social-connection';
      const label = document.createElement('span');
      label.textContent = `${provider[0].toUpperCase()}${provider.slice(1)} — ${details.linked ? 'Connected' : 'Not connected'}`;
      row.append(label);
      if (!details.linked && details.available) {
        const button = document.createElement('button');
        button.className = 'plain-button';
        button.type = 'button';
        button.textContent = 'Connect';
        button.addEventListener('click', () => startOAuth(provider, button));
        row.append(button);
      } else if (details.linked) {
        const button = document.createElement('button');
        button.className = 'plain-button';
        button.type = 'button';
        button.textContent = 'Disconnect';
        button.addEventListener('click', () => disconnectProvider(provider, button));
        row.append(button);
      }
      socialConnections.append(row);
    }
    document.getElementById('connected-signins').hidden = socialCount === 0;
    const connect = document.getElementById('connect-discord');
    connect.hidden = account.discord_linked || !account.discord_available;
    document.getElementById('disconnect-discord').hidden = !account.discord_linked;
    document.getElementById('discord-guidance').textContent = account.discord_linked
      ? 'Your Discord identity is connected. Manage tasks here, or open MHM in Discord for tasks, check-ins, and support.'
      : account.discord_available
        ? 'Manage tasks here, or connect Discord to bring MHM tasks, check-ins, and support there.'
        : 'Discord connection is not configured yet. Ask your MHM administrator for help.';
    accountContent.hidden = false;
    const socialProvider = socialResult && socialResult.endsWith('-connected') ? socialResult.slice(0, -10) : '';
    status.textContent = socialProvider ? `${socialProvider[0].toUpperCase()}${socialProvider.slice(1)} is connected to your MHM account.`
      : socialResult === 'in-use' ? 'That social account is already connected to another MHM account.'
        : socialResult === 'error' ? 'That social account could not be connected. Please try again.'
          : discordResult === 'connected' ? 'Discord is connected to your MHM account.'
      : discordResult === 'cancelled' ? 'Discord connection was canceled. You can try again whenever you are ready.'
      : discordResult === 'in-use' ? 'That Discord account is already connected to another MHM account.'
        : discordResult === 'account-linked' ? 'This MHM account already has a different Discord account connected.'
          : discordResult === 'error' ? 'Discord could not be connected. Please try again.' : '';
  } catch (error) { status.textContent = error.message; status.classList.add('is-error'); }
}
async function disconnectProvider(provider, button) {
  if (button.disabled || !window.confirm(`Disconnect ${provider} from your MHM account?`)) return;
  button.disabled = true;
  status.textContent = `Disconnecting ${provider}…`;
  status.classList.remove('is-error');
  try {
    const response = await fetch('/api/account/connections', {
      method: 'POST', credentials: 'same-origin', cache: 'no-store',
      headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ provider }),
    });
    const result = await response.json().catch(() => ({}));
    if (response.status === 401) { returnToLogin(); return; }
    if (!response.ok) throw new Error(result.error || `${provider} could not be disconnected.`);
    status.textContent = `${provider[0].toUpperCase()}${provider.slice(1)} was disconnected.`;
    await loadAccount();
  } catch (error) { status.textContent = error.message; status.classList.add('is-error'); button.disabled = false; }
}
async function startOAuth(provider, button) {
  if (button.disabled) return;
  button.disabled = true;
  status.textContent = `Opening ${provider}…`;
  status.classList.remove('is-error');
  try {
    const response = await fetch(`/api/auth/oauth/${provider}/start`, { credentials: 'same-origin', cache: 'no-store' });
    const result = await response.json().catch(() => ({}));
    if (!response.ok || !result.url) throw new Error(result.error || `${provider} connection is unavailable.`);
    location.assign(result.url);
  } catch (error) {
    status.textContent = error.message;
    status.classList.add('is-error');
    button.disabled = false;
  }
}
const connectDiscord = document.getElementById('connect-discord');
if (connectDiscord) connectDiscord.addEventListener('click', async (event) => {
  const button = event.currentTarget;
  if (button.disabled) return;
  button.disabled = true;
  status.textContent = 'Opening Discord…';
  status.classList.remove('is-error');
  try {
    const response = await fetch('/api/auth/discord/start', { credentials: 'same-origin', cache: 'no-store' });
    const result = await response.json().catch(() => ({}));
    if (!response.ok || !result.url) throw new Error(result.error || 'Discord connection is unavailable.');
    location.assign(result.url);
  } catch (error) {
    status.textContent = error.message;
    status.classList.add('is-error');
    button.disabled = false;
  }
});
const disconnectDiscord = document.getElementById('disconnect-discord');
if (disconnectDiscord) disconnectDiscord.addEventListener('click', event => disconnectProvider('discord', event.currentTarget));
const logout = document.getElementById('logout');
if (logout) logout.addEventListener('click', async (event) => {
  const button = event.currentTarget;
  if (button.disabled || !window.dispatchEvent(new Event('mhm:before-logout', { cancelable: true }))) return;
  button.disabled = true;
  status.classList.remove('is-error');
  try {
    const response = await fetch('/api/auth/logout', { method: 'POST', credentials: 'same-origin', cache: 'no-store', headers: { 'Content-Type': 'application/json' }, body: '{}', signal: AbortSignal.timeout(15000) });
    if (!response.ok && response.status !== 401) throw new Error('Could not log out. Please try again.');
    returnToLogin();
  } catch (error) { status.textContent = 'Could not log out. Please try again.'; status.classList.add('is-error'); button.disabled = false; }
});
const passwordForm = document.getElementById('password-form');
if (passwordForm) passwordForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const passwordStatus = document.getElementById('password-status');
  const first = document.getElementById('new-password');
  const confirmation = document.getElementById('new-password-confirm');
  const current = document.getElementById('current-password');
  const button = document.getElementById('save-password');
  if (first.value !== confirmation.value) {
    passwordStatus.textContent = 'Those passwords do not match.';
    passwordStatus.classList.add('is-error');
    return;
  }
  button.disabled = true;
  passwordStatus.textContent = 'Saving…';
  passwordStatus.classList.remove('is-error');
  try {
    const response = await fetch('/api/auth/password/setup', {
      method: 'POST', credentials: 'same-origin', cache: 'no-store',
      headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ password: first.value, current_password: current.value }),
    });
    const result = await response.json().catch(() => ({}));
    if (response.status === 401) { returnToLogin(); return; }
    if (!response.ok) throw new Error(result.error || 'Your password could not be saved.');
    first.value = '';
    confirmation.value = '';
    current.value = '';
    document.getElementById('current-password-field').hidden = false;
    current.required = true;
    document.getElementById('password-heading').textContent = 'Change your password.';
    document.getElementById('password-guidance').textContent = 'Your password is set. You can replace it here whenever you need to.';
    passwordStatus.textContent = 'Your password is saved.';
  } catch (error) {
    passwordStatus.textContent = error.message;
    passwordStatus.classList.add('is-error');
  } finally { button.disabled = false; }
});
if (accountContent) loadAccount();
