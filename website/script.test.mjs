import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';

const source = await readFile(new URL('./script.js', import.meta.url), 'utf8');

function page() {
  const classNames = new Set();
  const listeners = {};
  const windowListeners = {};
  const attrs = { 'aria-expanded': 'false' };
  const toggle = {
    textContent: 'Menu',
    getAttribute(name) { return attrs[name]; },
    setAttribute(name, value) { attrs[name] = value; },
    addEventListener(type, listener) { listeners[`toggle:${type}`] = listener; },
  };
  const menu = {
    classList: {
      toggle(name, force) {
        if (force) classNames.add(name);
        else classNames.delete(name);
      },
      contains(name) { return classNames.has(name); },
    },
    addEventListener(type, listener) { listeners[`menu:${type}`] = listener; },
  };
  vm.runInContext(source, vm.createContext({
    document: {
      getElementById(id) {
        if (id === 'year') return null;
        if (id === 'nav-toggle') return toggle;
        if (id === 'site-menu') return menu;
        return null;
      },
    },
    window: { addEventListener(type, listener) { windowListeners[type] = listener; } },
  }));
  return { toggle, classNames, listeners, windowListeners };
}

test('nav toggle opens and closes the compact menu', () => {
  const view = page();
  view.listeners['toggle:click']();
  assert.equal(view.toggle.getAttribute('aria-expanded'), 'true');
  assert.equal(view.classNames.has('is-open'), true);
  assert.equal(view.toggle.textContent, 'Close');
  view.listeners['toggle:click']();
  assert.equal(view.toggle.getAttribute('aria-expanded'), 'false');
  assert.equal(view.classNames.has('is-open'), false);
  assert.equal(view.toggle.textContent, 'Menu');
});

test('escape and choosing a destination close the compact menu', () => {
  const view = page();
  view.listeners['toggle:click']();
  view.windowListeners.keydown({ key: 'Escape' });
  assert.equal(view.toggle.getAttribute('aria-expanded'), 'false');
  view.listeners['toggle:click']();
  view.listeners['menu:click']({ target: { closest(selector) { return selector.includes('a') ? {} : null; } } });
  assert.equal(view.toggle.getAttribute('aria-expanded'), 'false');
  assert.equal(view.classNames.has('is-open'), false);
});
