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

test('notebook exposes active, pinned, inbox, and archived views without groups', () => {
  assert.doesNotMatch(html, /id="note-group"/);
  assert.match(html, /id="note-tabs"/);
  assert.match(html, /data-note-view="active"/);
  assert.match(html, /data-note-view="pinned"/);
  assert.match(html, /data-note-view="inbox"/);
  assert.match(html, /data-note-view="archived"/);
  assert.match(source, /status: view/);
  assert.doesNotMatch(source, /data-note-group/);
});

test('archived entries do not render a pinned quality', () => {
  assert.match(source, /note\.status === 'active' && note\.pinned/);
});
