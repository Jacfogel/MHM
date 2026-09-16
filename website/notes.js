(() => {
  const status = document.getElementById('notes-status');
  const workspace = document.getElementById('notes-workspace');
  const list = document.getElementById('note-list');
  const empty = document.getElementById('note-empty');
  const count = document.getElementById('notes-count');
  const account = document.getElementById('notes-account');
  const createForm = document.getElementById('note-create-form');
  const entryKind = document.getElementById('entry-kind');
  const descriptionField = document.getElementById('entry-description-field');
  const descriptionLabel = document.getElementById('entry-description-label');
  const listField = document.getElementById('entry-list-field');
  const createItems = document.getElementById('entry-create-items');
  const createSubmit = document.getElementById('entry-create-submit');
  const createHeading = document.getElementById('entry-create-heading');
  const createHelp = document.getElementById('entry-create-help');
  const search = document.getElementById('note-search');
  const tabs = [...document.querySelectorAll('[data-note-view]')];
  let view = 'active';
  let notes = [];
  let searchTimer;
  let itemId = 0;

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
      const error = new Error(result.error || 'MHM could not update your notebook. Please try again.');
      error.status = response.status;
      throw error;
    }
    return result;
  }

  function button(label, className, onClick) {
    const action = document.createElement('button');
    action.type = 'button';
    action.className = className;
    action.textContent = label;
    action.addEventListener('click', onClick);
    return action;
  }

  function input(parent, labelText, type, value, id) {
    const wrapper = document.createElement('div');
    wrapper.className = 'settings-field';
    const label = document.createElement('label');
    label.htmlFor = id;
    label.textContent = labelText;
    const field = type === 'textarea' ? document.createElement('textarea') : document.createElement('input');
    field.id = id;
    field.name = id;
    field.value = value || '';
    if (type === 'textarea') field.rows = 5;
    else field.type = type;
    wrapper.append(label, field);
    parent.append(wrapper);
    return field;
  }

  function addListItem(container, value = { text: '', done: false }) {
    const row = document.createElement('div');
    row.className = 'notebook-item-row';
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.checked = Boolean(value.done);
    checkbox.setAttribute('aria-label', 'Item completed');
    const textField = document.createElement('input');
    textField.type = 'text';
    textField.value = value.text || '';
    textField.required = true;
    textField.maxLength = 500;
    textField.placeholder = 'List item';
    textField.id = `notebook-item-${itemId += 1}`;
    const remove = button('Remove', 'plain-button notebook-item-remove', () => {
      row.remove();
      if (!container.children.length) addListItem(container);
    });
    row.append(checkbox, textField, remove);
    container.append(row);
    return textField;
  }

  function collectListItems(container) {
    return [...container.querySelectorAll('.notebook-item-row')].map(row => ({
      text: row.querySelector('input[type="text"]').value.trim(),
      done: row.querySelector('input[type="checkbox"]').checked,
    })).filter(item => item.text);
  }

  function syncCreateMode() {
    const kind = entryKind.value;
    const isList = kind === 'list';
    descriptionField.hidden = isList;
    listField.hidden = !isList;
    if (isList && !createItems.children.length) addListItem(createItems);
    const labels = {
      note: ['Capture something useful', 'Write it down now. You can shape it later.', 'Note', 'Save note'],
      journal_entry: ['Add a journal entry', 'Record what happened, how you felt, or what you want to remember.', 'Journal entry', 'Save journal'],
      list: ['Start a useful list', 'Add the items now, then check them off as you go.', '', 'Save list'],
    }[kind];
    createHeading.textContent = labels[0];
    createHelp.textContent = labels[1];
    descriptionLabel.textContent = labels[2];
    createSubmit.firstChild.textContent = `${labels[3]} `;
  }

  function render() {
    list.replaceChildren();
    count.textContent = `${notes.length} ${view} ${notes.length === 1 ? 'entry' : 'entries'}`;
    empty.hidden = notes.length !== 0;
    for (const note of notes) {
      const article = document.createElement('article');
      article.className = `note-card${view === 'archived' ? ' is-archived' : ''}`;
      const content = document.createElement('div');
      content.className = 'note-card-content';
      const type = document.createElement('span');
      type.className = `entry-kind entry-kind-${note.kind}`;
      type.textContent = note.kind === 'journal_entry' ? 'Journal' : note.kind === 'list' ? 'List' : 'Note';
      content.append(type);
      if (note.pinned) content.append(button('Pinned', 'entry-kind entry-pinned', () => pin(note, false)));
      const title = document.createElement('h3');
      title.textContent = note.title || 'Untitled entry';
      content.append(title);
      if (note.description) {
        const body = document.createElement('p');
        body.textContent = note.description;
        content.append(body);
      }
      if (note.kind === 'list' && Array.isArray(note.items)) {
        const items = document.createElement('ul');
        items.className = 'notebook-list-items';
        for (const item of note.items) {
          const listItem = document.createElement('li');
          listItem.classList.toggle('is-done', Boolean(item.done));
          listItem.textContent = item.text;
          items.append(listItem);
        }
        content.append(items);
      }
      const meta = document.createElement('div');
      meta.className = 'task-meta';
      if (note.group) {
        const group = document.createElement('span');
        group.textContent = note.group;
        meta.append(group);
      }
      if (note.tags?.length) {
        const tags = document.createElement('span');
        tags.textContent = `Tags: ${note.tags.join(', ')}`;
        meta.append(tags);
      }
      content.append(meta);
      const actions = document.createElement('div');
      actions.className = 'task-actions';
      if (note.status === 'active') {
        actions.append(button('Edit', 'plain-button', () => edit(note)));
        actions.append(button(note.pinned ? 'Unpin' : 'Pin', 'plain-button', () => pin(note, !note.pinned)));
        actions.append(button('Archive', 'button task-action-primary', () => archive(note, 'archive')));
      } else {
        actions.append(button('Restore', 'plain-button', () => archive(note, 'restore')));
      }
      article.append(content, actions);
      list.append(article);
    }
  }

  async function load() {
    try {
      const query = search.value.trim();
      const result = await api(`/api/notes?status=${view}${query ? `&q=${encodeURIComponent(query)}` : ''}`);
      notes = result.notes || [];
      workspace.hidden = false;
      showStatus('');
      render();
    } catch (error) {
      workspace.hidden = error.status === 403;
      showStatus(error.message, true);
    }
  }

  async function loadIdentity() {
    try {
      const result = await api('/api/account');
      account.textContent = `Signed in as ${result.preferred_name || result.email}`;
    } catch (error) {
      showStatus(error.message, true);
    }
  }

  async function archive(note, action) {
    try {
      await api(`/api/notes/${encodeURIComponent(note.id)}/${action}`, 'POST', {});
      await load();
    } catch (error) {
      showStatus(error.message, true);
    }
  }

  async function pin(note, pinned) {
    try {
      await api(`/api/notes/${encodeURIComponent(note.id)}`, 'PATCH', { pinned });
      await load();
    } catch (error) { showStatus(error.message, true); }
  }

  function edit(note) {
    const dialog = document.createElement('dialog');
    dialog.className = 'task-dialog';
    const heading = document.createElement('h2');
    heading.textContent = `Edit ${note.kind === 'journal_entry' ? 'journal entry' : note.kind}`;
    const form = document.createElement('form');
    form.className = 'task-edit-form';
    const title = input(form, 'Title', 'text', note.title, 'edit-note-title');
    title.required = true;
    title.maxLength = 200;
    let body;
    let editItems;
    if (note.kind === 'list') {
      const itemEditor = document.createElement('fieldset');
      itemEditor.className = 'notebook-item-editor';
      const legend = document.createElement('legend');
      legend.textContent = 'List items';
      editItems = document.createElement('div');
      editItems.className = 'notebook-item-edit-list';
      for (const item of note.items || []) addListItem(editItems, item);
      if (!editItems.children.length) addListItem(editItems);
      itemEditor.append(legend, editItems, button('+ Add item', 'plain-button notebook-add-item', () => addListItem(editItems).focus()));
      form.append(itemEditor);
    } else {
      body = input(form, note.kind === 'journal_entry' ? 'Journal entry' : 'Note', 'textarea', note.description, 'edit-note-body');
      body.maxLength = 10000;
    }
    const tags = input(form, 'Tags', 'text', note.tags?.join(', '), 'edit-note-tags');
    tags.maxLength = 1000;
    tags.placeholder = 'health, ideas, home';
    const group = input(form, 'Group', 'text', note.group, 'edit-note-group');
    group.maxLength = 50;
    const actions = document.createElement('div');
    actions.className = 'task-dialog-actions';
    const save = document.createElement('button');
    save.type = 'submit';
    save.className = 'button';
    save.textContent = 'Save changes';
    actions.append(button('Cancel', 'plain-button', () => dialog.close()), save);
    form.append(actions);
    dialog.append(heading, form);
    document.body.append(dialog);
    form.addEventListener('submit', async event => {
      event.preventDefault();
      const items = editItems ? collectListItems(editItems) : null;
      if (editItems && !items.length) {
        showStatus('Add at least one list item.', true);
        editItems.querySelector('input[type="text"]')?.focus();
        return;
      }
      save.disabled = true;
      try {
        const payload = {
          title: title.value.trim(),
          tags: tags.value.split(',').map(tag => tag.trim()).filter(Boolean),
          group: group.value.trim() || null,
          ...(editItems ? { items } : { description: body.value }),
        };
        await api(`/api/notes/${encodeURIComponent(note.id)}`, 'PATCH', payload);
        dialog.close();
        await load();
      } catch (error) {
        showStatus(error.message, true);
        save.disabled = false;
      }
    });
    dialog.addEventListener('close', () => dialog.remove(), { once: true });
    if (dialog.showModal) dialog.showModal();
    else dialog.setAttribute('open', '');
    title.focus();
  }

  createForm.addEventListener('submit', async event => {
    event.preventDefault();
    const submit = createForm.querySelector('button[type="submit"]');
    const form = new FormData(createForm);
    const kind = String(form.get('kind') || 'note');
    const items = kind === 'list' ? collectListItems(createItems) : null;
    if (kind === 'list' && !items.length) {
      showStatus('Add at least one list item.', true);
      createItems.querySelector('input[type="text"]')?.focus();
      return;
    }
    submit.disabled = true;
    showStatus(`Saving ${kind === 'journal_entry' ? 'journal entry' : kind}…`);
    try {
      await api('/api/notes', 'POST', {
        kind,
        title: String(form.get('title') || '').trim(),
        tags: String(form.get('tags') || '').split(',').map(tag => tag.trim()).filter(Boolean),
        group: String(form.get('group') || '').trim() || null,
        ...(kind === 'list' ? { items } : { description: String(form.get('description') || '') }),
      });
      createForm.reset();
      createItems.replaceChildren();
      syncCreateMode();
      showStatus('');
      await load();
    } catch (error) {
      showStatus(error.message, true);
    } finally {
      submit.disabled = false;
    }
  });

  entryKind.addEventListener('change', syncCreateMode);
  document.getElementById('entry-add-item').addEventListener('click', () => addListItem(createItems).focus());
  for (const tab of tabs) tab.addEventListener('click', () => {
    view = tab.dataset.noteView;
    tabs.forEach(item => item.setAttribute('aria-selected', String(item === tab)));
    load();
  });
  search.addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(load, 250);
  });
  document.getElementById('notes-refresh').addEventListener('click', load);
  window.addEventListener('focus', load);
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') load();
  });
  syncCreateMode();
  load();
  loadIdentity();
})();
