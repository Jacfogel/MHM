const status = document.getElementById('app-status');
const accountContent = document.getElementById('account-content');
let accountSessionEnded = false;
const discordResult = new URLSearchParams(location.search).get('discord');
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
    document.getElementById('account-name').textContent = account.username;
    document.getElementById('account-email').textContent = account.email;
    document.getElementById('account-timezone').textContent = account.timezone || 'Not set';
    document.getElementById('account-discord').textContent = account.discord_linked ? 'Connected' : 'Not connected yet';
    const connect = document.getElementById('connect-discord');
    connect.hidden = account.discord_linked || !account.discord_available;
    document.getElementById('discord-guidance').textContent = account.discord_linked
      ? 'Your Discord identity is connected. Manage tasks here, or open MHM in Discord for tasks, check-ins, and support.'
      : account.discord_available
        ? 'Manage tasks here, or connect Discord to bring MHM tasks, check-ins, and support there.'
        : 'Discord connection is not configured yet. Ask your MHM administrator for help.';
    accountContent.hidden = false;
    status.textContent = discordResult === 'connected' ? 'Discord is connected to your MHM account.'
      : discordResult === 'cancelled' ? 'Discord connection was canceled. You can try again whenever you are ready.'
      : discordResult === 'in-use' ? 'That Discord account is already connected to another MHM account.'
        : discordResult === 'account-linked' ? 'This MHM account already has a different Discord account connected.'
          : discordResult === 'error' ? 'Discord could not be connected. Please try again.' : '';
  } catch (error) { status.textContent = error.message; status.classList.add('is-error'); }
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
if (accountContent) loadAccount();
