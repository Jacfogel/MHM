/* Phone ownership and explicit consent, shared by setup and account settings. */
window.MHMWhatsApp = {
  async mount(parent, onState) {
    const box = document.createElement('section');
    box.className = 'whatsapp-connection';
    const heading = document.createElement('h3'); heading.textContent = 'WhatsApp connection';
    const phoneLabel = document.createElement('label'); phoneLabel.textContent = 'Mobile number (including country code)';
    const phone = document.createElement('input'); phone.type = 'tel'; phone.autocomplete = 'tel';
    phoneLabel.append(phone);
    const consentLabel = document.createElement('label');
    const consent = document.createElement('input'); consent.type = 'checkbox';
    consentLabel.append(consent, document.createTextNode(' I consent to MHM WhatsApp messages on this number. Reply STOP to opt out; START to resume.'));
    const start = document.createElement('button'); start.type = 'button'; start.textContent = 'Get connection code';
    const verify = document.createElement('button'); verify.type = 'button'; verify.textContent = 'I sent the WhatsApp message — verify phone'; verify.hidden = true;
    const disconnect = document.createElement('button'); disconnect.type = 'button'; disconnect.textContent = 'Disconnect WhatsApp'; disconnect.hidden = true;
    const status = document.createElement('p'); status.setAttribute('role', 'status');
    box.append(heading, phoneLabel, consentLabel, start, verify, disconnect, status); parent.append(box);
    let token = ''; let pendingPhone = '';
    const api = async (data) => {
      const response = await fetch('/api/whatsapp/enrollment', {
        credentials: 'same-origin', cache: 'no-store',
        ...(data ? {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)} : {}),
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.error || 'Could not confirm WhatsApp connection. Check saved settings before retrying.');
      return result;
    };
    start.addEventListener('click', async () => {
      start.disabled = true;
      try {
        const result = await api({action: 'start', phone: phone.value, consent: consent.checked});
        token = result.token; pendingPhone = phone.value;
        status.textContent = `From this phone, send LINK ${token} in WhatsApp to ${result.sender}. Then select verify. The code expires in 15 minutes.`;
        verify.hidden = false;
      } catch (error) { status.textContent = error.message; }
      finally { start.disabled = false; }
    });
    verify.addEventListener('click', async () => {
      verify.disabled = true;
      try {
        if (phone.value !== pendingPhone) throw new Error('The phone changed. Request a new connection code.');
        await api({action: 'connect', phone: phone.value, consent: consent.checked, token});
        token = ''; verify.hidden = true; disconnect.hidden = false;
        status.textContent = 'Phone connected. Choose WhatsApp delivery and save to use it.';
        onState({connected: true, eligible: true});
      } catch (error) { status.textContent = error.message; }
      finally { verify.disabled = false; }
    });
    disconnect.addEventListener('click', async () => {
      disconnect.disabled = true;
      try {
        await api({action: 'disconnect'});
        status.textContent = 'WhatsApp disconnected. Reload delivery settings to see your current channel.';
        disconnect.hidden = true; onState({connected: false});
      } catch (error) { status.textContent = error.message; }
      finally { disconnect.disabled = false; }
    });
    try {
      const info = await api(); phone.value = info.phone || '';
      consent.checked = Boolean(info.connected);
      onState(info);
      disconnect.hidden = !info.connected;
      start.disabled = !info.available || !info.eligible;
      status.textContent = !info.eligible ? 'WhatsApp requires an active paid WhatsApp plan ($20 CAD/month). Trial accounts can use Email or Discord.'
        : !info.available ? 'WhatsApp is not configured yet.'
        : info.connected ? 'Your verified phone is connected.' : 'Verify your phone before selecting WhatsApp delivery.';
    } catch (error) { start.disabled = true; status.textContent = error.message; }
  },
};
