(() => {
  const status = document.getElementById('tasks-status');
  const workspace = document.getElementById('tasks-workspace');
  const list = document.getElementById('task-list');
  const empty = document.getElementById('task-empty');
  const count = document.getElementById('tasks-count');
  const summary = document.getElementById('task-list-summary');
  const createForm = document.getElementById('task-create-form');
  const tabs = [...document.querySelectorAll('[data-task-view]')];
  let view = 'active';
  let tasks = [];

  function showStatus(message, error = false) {
    status.textContent = message;
    status.classList.toggle('is-error', error);
  }

  async function api(path, method = 'GET', payload) {
    const response = await fetch(path, {
      method,
      credentials: 'same-origin',
      cache: 'no-store',
      ...(payload === undefined ? {} : {
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      }),
    });
    const result = await response.json().catch(() => ({}));
    if (response.status === 401) {
      window.dispatchEvent(new Event('mhm:signed-out'));
      location.replace('login.html');
      throw new Error('Please log in again.');
    }
    if (!response.ok) {
      const error = new Error(result.error || 'MHM could not update your tasks. Please try again.');
      error.status = response.status;
      throw error;
    }
    return result;
  }

  function button(label, className, onClick) {
    const action = document.createElement('button');
    action.type = 'button'; action.className = className; action.textContent = label;
    action.addEventListener('click', onClick);
    return action;
  }

  function dueText(task) {
    if (!task.due_date) return 'No due date';
    return `Due ${task.due_date}${task.due_time ? ` at ${task.due_time}` : ''}`;
  }

  function recurrenceText(task) {
    const pattern = task.recurrence && task.recurrence.pattern;
    if (!pattern) return '';
    const interval = task.recurrence.interval || 1;
    return interval === 1 ? `Repeats ${pattern}` : `Repeats every ${interval} ${pattern}`;
  }

  function tagsText(task) {
    return Array.isArray(task.tags) && task.tags.length ? `Tags: ${task.tags.join(', ')}` : '';
  }

  function remindersText(task) {
    const reminders = Array.isArray(task.reminders) ? task.reminders : [];
    const periods = reminders.filter(item => item && item.kind === 'scheduled' && item.period).map(item => item.period);
    if (!periods.length) return '';
    const shown = periods.slice(0, 2).map(period => `${period.date} ${period.start_time}–${period.end_time}`);
    return `Reminders: ${shown.join(', ')}${periods.length > 2 ? ` (+${periods.length - 2} more)` : ''}`;
  }

  function addReminderRow(parent, period = {}) {
    const row = document.createElement('div'); row.className = 'task-reminder-row';
    const date = input(row, 'Date', 'date', period.date, `reminder-date-${Math.random().toString(36).slice(2)}`);
    const start = input(row, 'From', 'time', period.start_time, `reminder-start-${Math.random().toString(36).slice(2)}`);
    const end = input(row, 'To', 'time', period.end_time, `reminder-end-${Math.random().toString(36).slice(2)}`);
    const remove = button('Remove', 'plain-button task-reminder-remove', () => row.remove());
    row.append(remove); parent.append(row);
    return { date, start, end };
  }

  function readReminderPeriods(parent) {
    return [...parent.querySelectorAll('.task-reminder-row')].map(row => ({
      date: row.querySelector('input[type="date"]')?.value || '',
      start_time: row.querySelectorAll('input[type="time"]')[0]?.value || '',
      end_time: row.querySelectorAll('input[type="time"]')[1]?.value || '',
    })).filter(period => period.date || period.start_time || period.end_time);
  }

  function render() {
    list.replaceChildren();
    count.textContent = `${tasks.length} ${view === 'active' ? 'active' : 'completed'} ${tasks.length === 1 ? 'task' : 'tasks'}`;
    summary.textContent = view === 'active' ? 'Make room for the next small step.' : 'You did these.';
    empty.hidden = tasks.length !== 0;
    for (const task of tasks) {
      const article = document.createElement('article');
      article.className = `task-card${view === 'completed' ? ' is-completed' : ''}`;
      const content = document.createElement('div'); content.className = 'task-card-content';
      const title = document.createElement('h3'); title.textContent = task.title; content.append(title);
      if (task.description) { const description = document.createElement('p'); description.textContent = task.description; content.append(description); }
      const meta = document.createElement('div'); meta.className = 'task-meta';
      const due = document.createElement('span'); due.textContent = dueText(task); meta.append(due);
      const priority = document.createElement('span'); priority.className = `priority priority-${task.priority}`; priority.textContent = task.priority; meta.append(priority);
      const repeat = recurrenceText(task); if (repeat) { const recurring = document.createElement('span'); recurring.textContent = repeat; meta.append(recurring); }
      const tags = tagsText(task); if (tags) { const tagLabel = document.createElement('span'); tagLabel.textContent = tags; meta.append(tagLabel); }
      const reminders = remindersText(task); if (reminders) { const reminderLabel = document.createElement('span'); reminderLabel.textContent = reminders; meta.append(reminderLabel); }
      content.append(meta);
      const actions = document.createElement('div'); actions.className = 'task-actions';
      if (view === 'active') {
        actions.append(button('Edit', 'plain-button', () => openEditor(task)));
        actions.append(button('Complete', 'button task-action-primary', () => changeTask(task, 'complete')));
      } else {
        actions.append(button('Restore', 'plain-button', () => changeTask(task, 'restore')));
      }
      actions.append(button('Delete', 'plain-button task-delete', () => removeTask(task)));
      article.append(content, actions); list.append(article);
    }
  }

  async function load() {
    try {
      const result = await api(`/api/tasks?status=${view}`);
      tasks = result.tasks || [];
      workspace.hidden = false; showStatus(''); render();
    } catch (error) {
      workspace.hidden = error.status === 403;
      showStatus(error.message, true);
    }
  }

  async function changeTask(task, action) {
    try { await api(`/api/tasks/${encodeURIComponent(task.id)}/${action}`, 'POST', {}); await load(); }
    catch (error) { showStatus(error.message, true); }
  }

  async function removeTask(task) {
    if (!window.confirm(`Delete “${task.title}”? This cannot be undone.`)) return;
    try { await api(`/api/tasks/${encodeURIComponent(task.id)}`, 'DELETE', {}); await load(); }
    catch (error) { showStatus(error.message, true); }
  }

  function input(parent, labelText, type, value, id) {
    const wrapper = document.createElement('div'); wrapper.className = 'settings-field';
    const label = document.createElement('label'); label.htmlFor = id; label.textContent = labelText;
    const field = type === 'textarea' ? document.createElement('textarea') : document.createElement('input');
    field.id = id; field.name = id; field.value = value || '';
    if (type === 'textarea') field.rows = 3; else field.type = type;
    wrapper.append(label, field); parent.append(wrapper); return field;
  }

  function select(parent, labelText, value, id, options) {
    const wrapper = document.createElement('div'); wrapper.className = 'settings-field';
    const label = document.createElement('label'); label.htmlFor = id; label.textContent = labelText;
    const field = document.createElement('select'); field.id = id; field.name = id;
    for (const [optionValue, optionLabel] of options) {
      const option = document.createElement('option'); option.value = optionValue; option.textContent = optionLabel;
      field.append(option);
    }
    field.value = value || '';
    wrapper.append(label, field); parent.append(wrapper); return field;
  }

  function openEditor(task) {
    const dialog = document.createElement('dialog'); dialog.className = 'task-dialog';
    const heading = document.createElement('h2'); heading.textContent = 'Edit task';
    const form = document.createElement('form'); form.className = 'task-edit-form';
    const title = input(form, 'Task title', 'text', task.title, 'edit-title'); title.required = true; title.maxLength = 500;
    const description = input(form, 'Details', 'textarea', task.description, 'edit-description'); description.maxLength = 10000;
    const row = document.createElement('div'); row.className = 'task-form-row';
    const date = input(row, 'Due date', 'date', task.due_date, 'edit-due-date');
    const time = input(row, 'Time', 'time', task.due_time, 'edit-due-time');
    const priority = select(row, 'Priority', task.priority, 'edit-priority', [['low', 'Low'], ['medium', 'Medium'], ['high', 'High'], ['urgent', 'Urgent'], ['critical', 'Critical']]);
    form.append(row);
    const recurrence = select(form, 'Repeat pattern', task.recurrence && task.recurrence.pattern, 'edit-recurrence', [['', 'Does not repeat'], ['daily', 'Daily'], ['weekly', 'Weekly'], ['monthly', 'Monthly'], ['yearly', 'Yearly']]);
    const tags = input(form, 'Tags', 'text', Array.isArray(task.tags) ? task.tags.join(', ') : '', 'edit-tags');
    tags.maxLength = 1000; tags.placeholder = 'health, errands, home';
    const reminderFieldset = document.createElement('fieldset'); reminderFieldset.className = 'task-reminders';
    const reminderLegend = document.createElement('legend'); reminderLegend.textContent = 'Scheduled reminders'; reminderFieldset.append(reminderLegend);
    const reminderList = document.createElement('div'); reminderList.className = 'task-reminder-list'; reminderFieldset.append(reminderList);
    const addReminder = button('+ Add a reminder', 'plain-button', () => addReminderRow(reminderList)); reminderFieldset.append(addReminder);
    if (Array.isArray(task.reminders)) task.reminders.filter(item => item && item.kind === 'scheduled' && item.period).forEach(item => addReminderRow(reminderList, item.period));
    form.append(reminderFieldset);
    const actions = document.createElement('div'); actions.className = 'task-dialog-actions';
    actions.append(button('Cancel', 'plain-button', () => dialog.close()));
    const save = document.createElement('button'); save.type = 'submit'; save.className = 'button'; save.textContent = 'Save changes'; actions.append(save);
    form.append(actions); dialog.append(heading, form); document.body.append(dialog);
    form.addEventListener('submit', async event => {
      event.preventDefault(); save.disabled = true;
      try {
        await api(`/api/tasks/${encodeURIComponent(task.id)}`, 'PATCH', {
          title: title.value.trim(), description: description.value,
          due_date: date.value || null, due_time: time.value || null, priority: priority.value.trim().toLowerCase(),
          recurrence_pattern: recurrence.value.trim().toLowerCase() || null,
          tags: tags.value.split(',').map(tag => tag.trim()).filter(Boolean),
          reminder_periods: readReminderPeriods(reminderList),
        });
        dialog.close(); await load();
      } catch (error) { showStatus(error.message, true); save.disabled = false; }
    });
    dialog.addEventListener('close', () => dialog.remove(), { once: true });
    if (typeof dialog.showModal === 'function') dialog.showModal(); else dialog.setAttribute('open', '');
    title.focus();
  }

  createForm.addEventListener('submit', async event => {
    event.preventDefault();
    const submit = createForm.querySelector('button[type="submit"]'); submit.disabled = true; showStatus('Adding task…');
    const form = new FormData(createForm);
    try {
      await api('/api/tasks', 'POST', {
        title: String(form.get('title') || '').trim(), description: String(form.get('description') || ''),
        due_date: form.get('due_date') || null, due_time: form.get('due_time') || null,
        priority: form.get('priority') || 'medium', recurrence_pattern: form.get('recurrence_pattern') || null,
        tags: String(form.get('tags') || '').split(',').map(tag => tag.trim()).filter(Boolean),
        reminder_periods: readReminderPeriods(document.getElementById('task-reminder-list')),
      });
      createForm.reset(); document.getElementById('task-priority').value = 'medium'; document.getElementById('task-reminder-list').replaceChildren(); showStatus(''); await load();
    } catch (error) { showStatus(error.message, true); }
    finally { submit.disabled = false; }
  });
  document.getElementById('task-add-reminder').addEventListener('click', () => addReminderRow(document.getElementById('task-reminder-list')));
  for (const tab of tabs) tab.addEventListener('click', () => { view = tab.dataset.taskView; tabs.forEach(item => item.setAttribute('aria-selected', String(item === tab))); load(); });
  load();
})();
