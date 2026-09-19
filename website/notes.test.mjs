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

test('notebook uses tags instead of groups', () => {
  assert.doesNotMatch(html, /note-group|All groups|>Group</);
  assert.doesNotMatch(source, /groupFilter|existingGroups|note\.group/);
});

test('archived entries do not render a pinned quality', () => {
  assert.match(source, /note\.status === 'active' && note\.pinned/);
});
