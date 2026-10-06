import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const source = await readFile(new URL('./notes.js', import.meta.url), 'utf8');
const html = await readFile(new URL('./notes.html', import.meta.url), 'utf8');

test('notebook create and edit forms provide an existing-tags picker', () => {
  assert.match(html, /id="note-existing-tag"/);
  assert.match(source, /populateTagPicker\(document\.getElementById\('note-existing-tag'\), existingTags\)/);
  assert.match(source, /bindTagPicker\(tags, existingTag\)/);
});

test('notebook tabs are active, pinned, inbox, and archived', () => {
  assert.match(html, /id="note-tabs"/);
  assert.match(html, /data-note-view="active"/);
  assert.match(html, /data-note-view="pinned"/);
  assert.match(html, /data-note-view="inbox"/);
  assert.match(html, /data-note-view="archived"/);
});

test('archived entries do not render a pinned quality', () => {
  assert.match(source, /note\.status === 'active' && note\.pinned/);
});

test('notebook loading ignores stale search and tab responses', () => {
  assert.match(source, /const request = \+\+loadRequest/);
  assert.match(source, /requestedView !== view/);
  assert.match(source, /requestedQuery !== search\.value\.trim\(\)/);
  assert.match(source, /requestedTag !== tagFilter\.value/);
});

test('empty notebook searches explain the result and can clear filters', () => {
  assert.match(html, /id="note-empty-title"/);
  assert.match(html, /id="note-clear-filters"/);
  assert.match(source, /No matching entries\./);
  assert.match(source, /search\.value = ''/);
  assert.match(source, /tagFilter\.value = ''/);
});

test('notebook drafts and changed edit dialogs are protected from accidental dismissal', () => {
  assert.match(source, /function hasNoteDraft\(\)/);
  assert.match(source, /Discard your unsaved notebook changes/);
  assert.match(source, /mhm:before-logout/);
  assert.match(source, /beforeunload/);
  assert.match(source, /dialog\.addEventListener\('cancel'/);
  assert.match(source, /notebook-item-remove, \.notebook-add-item/);
});
