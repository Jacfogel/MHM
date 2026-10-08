const status = document.getElementById('app-status');
const accountContent = document.getElementById('account-content');
let accountSessionEnded = false;
const discordResult = new URLSearchParams(location.search).get('discord');
const socialResult = new URLSearchParams(location.search).get('social');
const billingResult = new URLSearchParams(location.search).get('billing');
window.addEventListener('mhm:signed-out', () => {
  accountSessionEnded = true;
  if (accountContent) accountContent.hidden = true;
});
function returnToLogin() {
  window.dispatchEvent(new Event('mhm:signed-out'));
  if (accountContent) accountContent.hidden = true;
  location.replace('login.html');
}
function setButtonBusy(button, busy) {
  button.disabled = busy;
  if (busy) button.setAttribute('aria-busy', 'true');
  else button.removeAttribute('aria-busy');
}
function renderBilling(billing) {
  const message = document.getElementById('billing-status');
  const subscribe = document.getElementById('start-subscription');
  const manage = document.getElementById('manage-billing');
  if (!message || !subscribe || !manage || !billing) return;
  subscribe.hidden = true;
  manage.hidden = true;
  const days = Number(billing.trial_days_remaining || 0);
  if (billing.status === 'comped') {
    message.textContent = 'Your account has complimentary access.';
  } else if (billing.status === 'trialing') {
    message.textContent = days > 0
      ? `Your free trial has ${days} day${days === 1 ? '' : 's'} remaining.`
      : 'Your free trial has ended. Subscribe to keep scheduled support active.';
    if (billing.subscription_exists || billing.customer_exists) manage.hidden = false;
    else if (billing.checkout_available) subscribe.hidden = false;
  } else if (billing.status === 'active') {
    message.textContent = 'Your monthly MHM subscription is active.';
    manage.hidden = !billing.customer_exists;
  } else if (billing.status === 'past_due') {
    message.textContent = billing.access_active
      ? 'Your latest payment needs attention. Scheduled support remains active during the short grace period.'
      : 'Scheduled support is paused because the latest payment was not completed.';
    manage.hidden = !billing.customer_exists;
  } else {
    message.textContent = 'Scheduled support is paused. Subscribe to start it again.';
    if (billing.checkout_available) subscribe.hidden = false;
    manage.hidden = !billing.customer_exists;
  }
  if (!billing.checkout_available && !billing.customer_exists && billing.status !== 'comped') {
    message.textContent += ' Billing is not available yet; please contact MHM support.';
  }
}
async function openBilling(endpoint, button) {
  if (!button || button.disabled) return;
  setButtonBusy(button, true);
  status.textContent = 'Opening secure billing…';
  status.classList.remove('is-error');
  try {
    const response = await fetch(endpoint, {
      method: 'POST', credentials: 'same-origin', cache: 'no-store',
      headers: { 'Content-Type': 'application/json' }, body: '{}',
    });
    const result = await response.json().catch(() => ({}));
    if (response.status === 401) { returnToLogin(); return; }
    if (!response.ok || !result.url) throw new Error(result.error || 'Billing could not open.');
    location.assign(result.url);
  } catch (error) {
    status.textContent = error.message;
    status.classList.add('is-error');
    setButtonBusy(button, false);
  }
}
async function loadAccount() {
  if (!accountContent) return;
  try {
    const response = await fetch('/api/account', { credentials: 'same-origin', cache: 'no-store' });
    if (response.status === 401) { returnToLogin(); return; }
    if (!response.ok) throw new Error('Your account could not load. Please refresh to try again.');
    const account = await response.json();
    if (accountSessionEnded) return;
    const accountName = document.getElementById('account-name');
    if (accountName) accountName.textContent = account.preferred_name || 'there';
    const accountEmail = document.getElementById('account-email');
    if (accountEmail) accountEmail.textContent = account.email;
    renderBilling(account.billing);
    const passwordHeading = document.getElementById('password-heading');
    if (passwordHeading) {
      passwordHeading.textContent = account.password_set ? 'Change your password.' : 'Set a password.';
      document.getElementById('password-guidance').textContent = account.password_set
        ? 'Your password is set. You can replace it here whenever you need to.'
        : 'Add a password so your next sign-in does not need an emailed code.';
      document.getElementById('current-password-field').hidden = !account.password_change_requires_current;
      document.getElementById('current-password').required = account.password_change_requires_current;
    }
    accountContent.hidden = false;
    const socialProvider = socialResult && socialResult.endsWith('-connected') ? socialResult.slice(0, -10) : '';
    status.textContent = billingResult === 'success' ? 'Your secure checkout is complete. Billing status may take a moment to update.'
      : billingResult === 'cancelled' ? 'Checkout was canceled. Your plan has not changed.'
      : socialProvider ? `${socialProvider[0].toUpperCase()}${socialProvider.slice(1)} is connected to your MHM account.`
      : socialResult === 'in-use' ? 'That social account is already connected to another MHM account.'
        : socialResult === 'error' ? 'That social account could not be connected. Please try again.'
          : discordResult === 'connected' ? 'Discord is connected to your MHM account.'
      : discordResult === 'cancelled' ? 'Discord connection was canceled. You can try again whenever you are ready.'
      : discordResult === 'in-use' ? 'That Discord account is already connected to another MHM account.'
        : discordResult === 'account-linked' ? 'This MHM account already has a different Discord account connected.'
          : discordResult === 'unavailable' ? 'Discord connection is not configured right now. Please ask your MHM administrator for help.'
            : discordResult === 'error' ? 'Discord could not be connected. This can happen when that Discord account is already linked to another MHM account. Disconnect it from the other account first, or try again; if it still fails, ask your MHM administrator for help.' : '';
    const socialConnections = document.getElementById('social-connections');
    if (!socialConnections) return;
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
  } catch (error) { status.textContent = error.message; status.classList.add('is-error'); }
}
const startSubscription = document.getElementById('start-subscription');
if (startSubscription) startSubscription.addEventListener('click', event => openBilling('/api/billing/checkout', event.currentTarget));
const manageBilling = document.getElementById('manage-billing');
if (manageBilling) manageBilling.addEventListener('click', event => openBilling('/api/billing/portal', event.currentTarget));
async function disconnectProvider(provider, button) {
  if (button.disabled || !window.confirm(`Disconnect ${provider} from your MHM account?`)) return;
  setButtonBusy(button, true);
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
    await loadAccount();
    status.textContent = `${provider[0].toUpperCase()}${provider.slice(1)} was disconnected.`;
    status.classList.remove('is-error');
  } catch (error) { status.textContent = error.message; status.classList.add('is-error'); setButtonBusy(button, false); }
}
async function startOAuth(provider, button) {
  if (button.disabled) return;
  setButtonBusy(button, true);
  status.textContent = `Opening ${provider}…`;
  status.classList.remove('is-error');
  try {
    const response = await fetch(`/api/auth/oauth/${provider}/start`, { credentials: 'same-origin', cache: 'no-store' });
    const result = await response.json().catch(() => ({}));
    if (response.status === 401) { returnToLogin(); return; }
    if (!response.ok || !result.url) throw new Error(result.error || `${provider} connection is unavailable.`);
    location.assign(result.url);
  } catch (error) {
    status.textContent = error.message;
    status.classList.add('is-error');
    setButtonBusy(button, false);
  }
}
const connectDiscord = document.getElementById('connect-discord');
if (connectDiscord) connectDiscord.addEventListener('click', async (event) => {
  const button = event.currentTarget;
  if (button.disabled) return;
  setButtonBusy(button, true);
  status.textContent = 'Opening Discord…';
  status.classList.remove('is-error');
  try {
    const response = await fetch('/api/auth/discord/start', { credentials: 'same-origin', cache: 'no-store' });
    const result = await response.json().catch(() => ({}));
    if (response.status === 401) { returnToLogin(); return; }
    if (!response.ok || !result.url) throw new Error(result.error || 'Discord connection is unavailable.');
    location.assign(result.url);
  } catch (error) {
    status.textContent = error.message;
    status.classList.add('is-error');
    setButtonBusy(button, false);
  }
});
const disconnectDiscord = document.getElementById('disconnect-discord');
if (disconnectDiscord) disconnectDiscord.addEventListener('click', event => disconnectProvider('discord', event.currentTarget));
const logout = document.getElementById('logout');
if (logout) logout.addEventListener('click', async (event) => {
  const button = event.currentTarget;
  if (button.disabled || !window.dispatchEvent(new Event('mhm:before-logout', { cancelable: true }))) return;
  setButtonBusy(button, true);
  status.classList.remove('is-error');
  try {
    const response = await fetch('/api/auth/logout', { method: 'POST', credentials: 'same-origin', cache: 'no-store', headers: { 'Content-Type': 'application/json' }, body: '{}', signal: AbortSignal.timeout(15000) });
    if (!response.ok && response.status !== 401) throw new Error('Could not log out. Please try again.');
    returnToLogin();
  } catch (error) { status.textContent = 'Could not log out. Please try again.'; status.classList.add('is-error'); setButtonBusy(button, false); }
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
  setButtonBusy(button, true);
  passwordForm.setAttribute('aria-busy', 'true');
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
  } finally { setButtonBusy(button, false); passwordForm.removeAttribute('aria-busy'); }
});
const deleteForm = document.getElementById('delete-account-form');
const deleteConfirm = document.getElementById('delete-confirm');
const deleteButton = document.getElementById('delete-account');
const deleteStatus = document.getElementById('delete-status');
if (deleteConfirm && deleteButton) {
  deleteConfirm.addEventListener('input', () => {
    deleteButton.disabled = deleteConfirm.value !== 'DELETE';
  });
}
if (deleteForm) deleteForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!deleteButton || deleteButton.disabled || deleteConfirm.value !== 'DELETE') return;
  setButtonBusy(deleteButton, true);
  deleteForm.setAttribute('aria-busy', 'true');
  deleteStatus.textContent = 'Deleting your account…';
  deleteStatus.classList.remove('is-error');
  try {
    const response = await fetch('/api/account/delete', {
      method: 'POST', credentials: 'same-origin', cache: 'no-store',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ confirmation: 'DELETE' }),
    });
    const result = await response.json().catch(() => ({}));
    if (response.status === 401) { returnToLogin(); return; }
    if (!response.ok) throw new Error(result.error || 'Your account could not be deleted.');
    window.dispatchEvent(new Event('mhm:signed-out'));
    location.replace('login.html');
  } catch (error) {
    deleteStatus.textContent = error.message;
    deleteStatus.classList.add('is-error');
    setButtonBusy(deleteButton, false);
    deleteButton.disabled = deleteConfirm.value !== 'DELETE';
    deleteForm.removeAttribute('aria-busy');
  }
});
if (accountContent) loadAccount();
