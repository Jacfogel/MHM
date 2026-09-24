(() => {
  const category = document.getElementById('message-category');
  const status = document.getElementById('messages-status');
  const workspace = document.getElementById('messages-workspace');
  const form = document.getElementById('message-form');
  const text = document.getElementById('message-text');
  const active = document.getElementById('message-active');
  const daysBox = document.getElementById('message-days');
  const periodsBox = document.getElementById('message-periods');
  const list = document.getElementById('message-list');
  const empty = document.getElementById('messages-empty');
  const summary = document.getElementById('messages-summary');
  const cancel = document.getElementById('message-cancel');
  const previewText = document.getElementById('message-preview-text');
  const previewMeta = document.getElementById('message-preview-meta');
  const dayChoices = [['ALL', 'Every day'], ['MONDAY', 'Monday'], ['TUESDAY', 'Tuesday'], ['WEDNESDAY', 'Wednesday'], ['THURSDAY', 'Thursday'], ['FRIDAY', 'Friday'], ['SATURDAY', 'Saturday'], ['SUNDAY', 'Sunday']];
  let messages = [];
  let editing = null;

  function showStatus(message, error = false) {
    status.textContent = message;
    status.classList.toggle('is-error', error);
  }
  async function api(path, method = 'GET', payload) {
    const response = await fetch(path, {
      method, credentials: 'same-origin', cache: 'no-store',
      ...(payload === undefined ? {} : { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }),
    });
    const result = await response.json().catch(() => ({}));
    if (response.status === 401) { window.dispatchEvent(new Event('mhm:signed-out')); location.replace('login.html'); throw new Error('Please log in again.'); }
    if (!response.ok) throw new Error(result.error || 'MHM could not update your messages. Please try again.');
    return result;
  }
  function checkbox(parent, value, labelText, checked) {
    const label = document.createElement('label');
    const input = document.createElement('input'); input.type = 'checkbox'; input.value = value; input.checked = checked;
    label.append(input, document.createTextNode(labelText)); parent.append(label); return input;
  }
  function choiceChecked(selectedValues, value, specificValues) {
    if (selectedValues.includes('ALL')) return true;
    if (value === 'ALL') return specificValues.length > 0 && specificValues.every(item => selectedValues.includes(item));
    return selectedValues.includes(value);
  }
  function renderChoices(periodNames, selectedDays = ['ALL'], selectedPeriods = ['ALL']) {
    daysBox.replaceChildren(); periodsBox.replaceChildren();
    const dayValues = dayChoices.slice(1).map(([value]) => value);
    for (const [value, label] of dayChoices) checkbox(daysBox, value, label, choiceChecked(selectedDays, value, dayValues));
    checkbox(periodsBox, 'ALL', 'Any reminder window', choiceChecked(selectedPeriods, 'ALL', periodNames));
    for (const name of periodNames) checkbox(periodsBox, name, name, choiceChecked(selectedPeriods, name, periodNames));
  }
  function syncAllChoice(parent, changed) {
    const boxes = [...parent.querySelectorAll('input')];
    const all = boxes.find(input => input.value === 'ALL');
    const rest = boxes.filter(input => input.value !== 'ALL');
    if (!all || changed.type !== 'checkbox') return;
    if (changed === all) {
      for (const box of rest) box.checked = all.checked;
      return;
    }
    all.checked = rest.length > 0 && rest.every(box => box.checked);
  }
  function selected(parent) {
    const values = [...parent.querySelectorAll('input:checked')].map(input => input.value);
    return values.includes('ALL') ? ['ALL'] : values;
  }
  function updatePreview() {
    previewText.textContent = text.value.trim() || 'Your message preview will appear here.';
    const days = selected(daysBox); const periods = selected(periodsBox);
    previewMeta.replaceChildren();
    for (const value of [active.checked ? 'Enabled' : 'Paused', `Days: ${days.length ? days.join(', ') : 'none selected'}`, `Windows: ${periods.length ? periods.join(', ') : 'none selected'}`]) {
      const item = document.createElement('span'); item.textContent = value; previewMeta.append(item);
    }
  }
  const extraFields = document.getElementById('message-extra-fields');
  const moreOptions = document.getElementById('message-more-options');
  function setExtraOpen(open) {
    extraFields.hidden = !open;
    moreOptions.setAttribute('aria-expanded', String(open));
    moreOptions.textContent = open ? 'Fewer options' : 'More options';
  }
  function resetForm(periodNames = []) {
    editing = null; form.reset(); active.checked = true;
    document.getElementById('message-form-title').textContent = 'Add a message'; cancel.hidden = true;
    renderChoices(periodNames);
    setExtraOpen(false);
    updatePreview();
  }
  function edit(message, periodNames) {
    editing = message; text.value = message.text; active.checked = message.active;
    document.getElementById('message-form-title').textContent = 'Edit message'; cancel.hidden = false;
    renderChoices(periodNames, message.days, message.periods);
    setExtraOpen(true);
    text.focus();
    updatePreview();
  }
  function render(periodNames) {
    list.replaceChildren(); summary.textContent = `${messages.length} personal ${messages.length === 1 ? 'message' : 'messages'}`; empty.hidden = messages.length !== 0;
    for (const message of messages) {
      const card = document.createElement('article'); card.className = 'note-card';
      const content = document.createElement('div'); content.className = 'note-card-content';
      const body = document.createElement('p'); body.textContent = message.text;
      const meta = document.createElement('div'); meta.className = 'task-meta';
      for (const value of [message.active ? 'Enabled' : 'Paused', `Days: ${message.days.join(', ')}`, `Windows: ${message.periods.join(', ')}`]) { const item = document.createElement('span'); item.textContent = value; meta.append(item); }
      content.append(body, meta);
      const actions = document.createElement('div'); actions.className = 'task-actions';
      const editButton = document.createElement('button'); editButton.type = 'button'; editButton.className = 'plain-button'; editButton.textContent = 'Edit'; editButton.addEventListener('click', () => edit(message, periodNames));
      const remove = document.createElement('button'); remove.type = 'button'; remove.className = 'plain-button task-delete'; remove.textContent = 'Delete'; remove.addEventListener('click', () => deleteMessage(message));
      actions.append(editButton, remove); card.append(content, actions); list.append(card);
    }
  }
  async function load(selectedCategory = category.value) {
    try {
      const query = selectedCategory ? `?category=${encodeURIComponent(selectedCategory)}` : '';
      const result = await api(`/api/messages${query}`);
      if (!category.options.length) for (const name of result.categories) { const option = document.createElement('option'); option.value = name; option.textContent = name.replaceAll('_', ' '); category.append(option); }
      category.value = result.category; messages = result.messages || []; workspace.hidden = false; resetForm(result.period_names); render(result.period_names); showStatus('');
      form.dataset.periodNames = JSON.stringify(result.period_names || []);
    } catch (error) { showStatus(error.message, true); }
  }
  async function deleteMessage(message) {
    if (!window.confirm('Delete this personal message? This cannot be undone.')) return;
    try { await api(`/api/messages/${encodeURIComponent(category.value)}/${encodeURIComponent(message.id)}`, 'DELETE', {}); await load(category.value); }
    catch (error) { showStatus(error.message, true); }
  }
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const payload = { text: text.value, active: active.checked, days: selected(daysBox), periods: selected(periodsBox) };
    const submit = form.querySelector('button[type="submit"]'); submit.disabled = true;
    try {
      if (editing) await api(`/api/messages/${encodeURIComponent(category.value)}/${encodeURIComponent(editing.id)}`, 'PATCH', payload);
      else await api(`/api/messages?category=${encodeURIComponent(category.value)}`, 'POST', payload);
      await load(category.value);
    } catch (error) { showStatus(error.message, true); }
    finally { submit.disabled = false; }
  });
  cancel.addEventListener('click', () => resetForm(JSON.parse(form.dataset.periodNames || '[]')));
  form.addEventListener('input', updatePreview);
  form.addEventListener('change', event => {
    if (event.target instanceof HTMLInputElement && event.target.type === 'checkbox') {
      const parent = event.target.closest('#message-days, #message-periods');
      if (parent) syncAllChoice(parent, event.target);
    }
    updatePreview();
  });
  moreOptions.addEventListener('click', () => setExtraOpen(extraFields.hidden));
  document.getElementById('message-test').addEventListener('click', async () => {
    try {
      const result = await api('/api/actions', 'POST', { action: 'test_message', category: category.value });
      showStatus(result.message || 'Your test message was queued.');
    } catch (error) { showStatus(error.message, true); }
  });
  category.addEventListener('change', () => load(category.value));
  load();
})();
