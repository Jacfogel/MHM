import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';

const source = await readFile(new URL('./tasks.js', import.meta.url), 'utf8');
const helperSource = `${source.slice(0, source.indexOf('(() =>'))}\nthis.helpers = MHMTaskInput;`;
const context = vm.createContext({});
vm.runInContext(helperSource, context);

test('task help asks for smaller steps instead of replacing the title', () => {
  assert.match(source, /Suggest smaller steps/);
  assert.match(source, /\/breakdown/);
  assert.match(source, /'subtasks'/);
  assert.match(source, /task-step-title/);
  assert.match(source, /Make this its own task/);
  assert.match(source, /restore_steps/);
  assert.doesNotMatch(source, /simplify-title/);
});

test('existing task tags append without duplicates', () => {
  assert.equal(context.helpers.withTag('health, home', 'work'), 'health, home, work');
  assert.equal(context.helpers.withTag('health, home', 'HEALTH'), 'health, home');
  assert.equal(context.helpers.withTag('', 'personal'), 'personal');
});

test('blank template selection resets all create-form fields', () => {
  assert.match(source, /const templateId = event\.target\.value;[\s\S]*resetCreateForm\(\);[\s\S]*if \(!template\)/);
  assert.match(source, /function resetCreateForm\(\) \{[\s\S]*createForm\.reset\(\);[\s\S]*task-reminder-list[\s\S]*setExtraFieldsOpen\(false\)/);
});

test('extra create fields stay collapsed until More options is opened', () => {
  assert.match(source, /function setExtraFieldsOpen\(open\) \{[\s\S]*extraFields\.hidden = !open;[\s\S]*Fewer options/);
  assert.match(source, /moreOptions\.addEventListener\('click', \(\) => setExtraFieldsOpen\(extraFields\.hidden\)\)/);
  assert.match(source, /if \(!template\) \{ setExtraFieldsOpen\(false\);[\s\S]*setExtraFieldsOpen\(true\);/);
});

test('selected active tasks can receive one priority in bulk', async () => {
  const html = await readFile(new URL('./tasks.html', import.meta.url), 'utf8');
  assert.match(html, /id="task-bulk-priority"/);
  assert.match(html, /id="task-bulk-priority-apply"/);
  assert.match(source, /runBulk\('priority', \{ priority: bulkPriority\.value \}\)/);
  assert.match(source, /bulkPriorityControls\.hidden = view !== 'active'/);
  assert.match(source, /action !== 'priority' && !window\.confirm/);
});

test('task list supports selecting or clearing every visible task', async () => {
  const html = await readFile(new URL('./tasks.html', import.meta.url), 'utf8');
  assert.match(html, /id="task-select-all"/);
  assert.match(source, /tasks\.every\(task => selected\.has\(task\.id\)\)/);
  assert.match(source, /allSelected \? 'Clear selection' : 'Select all'/);
  assert.match(source, /tasks\.forEach\(task => selected\.add\(task\.id\)\)/);
});

test('task loading ignores responses for an older view', () => {
  assert.match(source, /const request = \+\+loadRequest/);
  assert.match(source, /if \(request !== loadRequest \|\| requestedView !== view\) return/);
});

test('due-soon summary stays quiet when it has nothing useful to say', () => {
  assert.match(source, /dueSoon\.hidden = view !== 'active' \|\| dueSoonCount === 0/);
});

test('task drafts and changed edit dialogs are protected from accidental dismissal', () => {
  assert.match(source, /function hasTaskDraft\(\)/);
  assert.match(source, /Discard your unsaved task changes/);
  assert.match(source, /mhm:before-logout/);
  assert.match(source, /beforeunload/);
  assert.match(source, /dialog\.addEventListener\('cancel'/);
  assert.match(source, /task-reminder-add, \.task-reminder-remove/);
});
