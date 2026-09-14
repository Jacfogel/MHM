const status = document.getElementById('app-status');
let accountSessionEnded = false;
window.addEventListener('mhm:signed-out', () => {
  accountSessionEnded = true;
  document.getElementById('account-content').hidden = true;
});
function returnToLogin() {
  window.dispatchEvent(new Event('mhm:signed-out'));
  document.getElementById('account-content').hidden = true;
  location.replace('login.html');
}
async function loadAccount() {
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
    if (account.discord_url) {
      const link = document.getElementById('open-discord');
      link.href = account.discord_url;
      link.hidden = false;
      document.getElementById('discord-guidance').textContent = account.discord_linked
        ? 'Open your MHM conversation for tasks, check-ins, and support.'
        : 'Open MHM in Discord and choose “Link account”. Use your MHM username and the code sent to your email.';
    }
    document.getElementById('account-content').hidden = false;
    status.textContent = '';
  } catch (error) { status.textContent = error.message; status.classList.add('is-error'); }
}
document.getElementById('logout').addEventListener('click', async (event) => {
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
loadAccount();
