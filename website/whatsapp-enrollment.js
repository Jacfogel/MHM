/* Phone ownership and explicit consent, shared by setup and account settings. */
window.MHMWhatsApp = {
  async mount(parent, onState) {
    const box = document.createElement('section');
    box.className = 'whatsapp-connection';
    const heading = document.createElement('h3'); heading.textContent = 'WhatsApp connection';
    const phoneLabel = document.createElement('label'); phoneLabel.textContent = 'Mobile number (including country code)';
    phoneLabel.className = 'settings-field';
    const phone = document.createElement('input'); phone.type = 'tel'; phone.autocomplete = 'tel';
    phone.inputMode = 'tel'; phone.maxLength = 40; phone.placeholder = '+1 306 555 0123';
    phone.addEventListener('blur', () => {
      const number = window.MHMPhoneInput.normalize(phone.value);
      if (number) phone.value = number;
    });
    phoneLabel.append(phone);
    const consentLabel = document.createElement('label');
    consentLabel.className = 'phone-consent';
    const consent = document.createElement('input'); consent.type = 'checkbox';
    consentLabel.append(consent, document.createTextNode(' I consent to MHM WhatsApp messages on this number. Reply STOP to opt out; START to resume.'));
    const start = document.createElement('button'); start.type = 'button'; start.textContent = 'Get connection code'; start.disabled = true;
    const verify = document.createElement('button'); verify.type = 'button'; verify.textContent = 'I sent the WhatsApp message — verify phone'; verify.hidden = true;
    const disconnect = document.createElement('button'); disconnect.type = 'button'; disconnect.textContent = 'Disconnect WhatsApp'; disconnect.hidden = true;
    const status = document.createElement('p'); status.setAttribute('role', 'status');
    box.append(heading, phoneLabel, consentLabel, start, verify, disconnect, status); parent.append(box);
    for (const button of [start, verify, disconnect]) button.className = 'button button-small';
    status.className = 'form-status';
    let token = ''; let pendingPhone = '';
    const api = async (data) => {
      const recovery = data ? 'Could not confirm the phone connection change. Keep your entries and refresh the connection to check saved state before retrying.' : 'Could not load the phone connection. Refresh the connection to try again, or choose Email or Discord.';
      const response = await fetch('/api/whatsapp/enrollment', {
        credentials: 'same-origin', cache: 'no-store',
        ...(data ? {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)} : {}),
      }).catch(() => { throw new Error(recovery); });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(response.status === 400 && result.error && !/^\d{3}[: ]/.test(result.error) ? result.error : recovery);
      return result;
    };
    start.addEventListener('click', async () => {
      start.disabled = true;
      status.className = 'form-status';
      try {
        const number = window.MHMPhoneInput.validate(phone);
        if (!consent.checked) throw new Error('Please confirm your consent before requesting a connection code.');
        const result = await api({action: 'start', phone: number, consent: consent.checked});
        token = result.token; pendingPhone = phone.value;
        status.textContent = `From this phone, send LINK ${token} in WhatsApp to ${result.sender}. Then select verify. The code expires in 15 minutes.`;
        verify.hidden = false;
      } catch (error) { status.className = 'form-status is-error'; status.textContent = error.message; }
      finally { start.disabled = false; }
    });
    verify.addEventListener('click', async () => {
      verify.disabled = true;
      status.className = 'form-status';
      try {
        const number = window.MHMPhoneInput.validate(phone);
        if (number !== pendingPhone) throw new Error('The phone changed. Request a new connection code.');
        if (!consent.checked) throw new Error('Please confirm your consent before connecting this phone.');
        await api({action: 'connect', phone: number, consent: consent.checked, token});
        token = ''; verify.hidden = true; disconnect.hidden = false;
        status.textContent = 'Phone connected. Choose WhatsApp delivery and save to use it.';
        onState({connected: true, eligible: true});
      } catch (error) { status.className = 'form-status is-error'; status.textContent = error.message; }
      finally { verify.disabled = false; }
    });
    disconnect.addEventListener('click', async () => {
      disconnect.disabled = true;
      status.className = 'form-status';
      try {
        await api({action: 'disconnect'});
        status.textContent = 'WhatsApp disconnected. Reload delivery settings to see your current channel.';
        disconnect.hidden = true; onState({connected: false});
      } catch (error) { status.className = 'form-status is-error'; status.textContent = error.message; }
      finally { disconnect.disabled = false; }
    });
    async function refresh() {
      try {
        const info = await api();
        if (!phone.value) phone.value = info.phone || '';
        consent.checked = Boolean(info.connected);
        disconnect.hidden = !info.connected;
        start.disabled = !info.available || !info.eligible;
        if (!start.dataset) start.dataset = {};
        start.dataset.unavailable = String(start.disabled);
        status.className = 'form-status';
        status.textContent = !info.eligible ? 'WhatsApp requires an active paid WhatsApp plan ($20 CAD/month). Trial accounts can use Email or Discord.'
          : !info.available ? 'WhatsApp is not configured yet.'
          : info.connected ? 'Your verified phone is connected.' : 'Verify your phone before selecting WhatsApp delivery.';
        onState(info);
      } catch (error) {
        onState({failed: true});
        if (!start.dataset) start.dataset = {};
        start.dataset.unavailable = 'true';
        start.disabled = true;
        status.className = 'form-status is-error';
        status.textContent = error.message;
      }
    }
    const retry = document.createElement('button');
    retry.type = 'button'; retry.className = 'plain-button'; retry.textContent = 'Refresh connection';
    retry.addEventListener('click', async () => { retry.disabled = true; try { await refresh(); } finally { retry.disabled = false; } });
    box.append(retry);
    await refresh();
  },
};
