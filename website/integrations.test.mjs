import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const source = await readFile(new URL('./integrations.js', import.meta.url), 'utf8');

test('health actions disable every integration control while saving', () => {
  assert.match(source, /if \(healthBusy\) return/);
  assert.match(source, /for \(const button of healthButtons\) button\.disabled = busy/);
  assert.match(source, /healthCard\.setAttribute\('aria-busy', 'true'\)/);
  assert.match(source, /healthCard\.removeAttribute\('aria-busy'\)/);
});

test('blocked health connection popups fall back to the current tab', () => {
  assert.match(source, /const opened = window\.open\(result\.url, '_blank'\)/);
  assert.match(source, /if \(opened\) opened\.opener = null/);
  assert.match(source, /else location\.assign\(result\.url\)/);
});
