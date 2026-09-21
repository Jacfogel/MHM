const year = document.getElementById('year');
if (year) year.textContent = new Date().getFullYear();

const navToggle = document.getElementById('nav-toggle');
const siteMenu = document.getElementById('site-menu');
if (navToggle && siteMenu) {
  function setMenuOpen(open) {
    navToggle.setAttribute('aria-expanded', String(open));
    siteMenu.classList.toggle('is-open', open);
    navToggle.textContent = open ? 'Close' : 'Menu';
  }
  navToggle.addEventListener('click', () => setMenuOpen(navToggle.getAttribute('aria-expanded') !== 'true'));
  siteMenu.addEventListener('click', event => {
    const target = event.target && typeof event.target.closest === 'function' ? event.target : event.target.parentElement;
    if (target && typeof target.closest === 'function' && target.closest('a, button')) setMenuOpen(false);
  });
  window.addEventListener('keydown', event => {
    if (event.key === 'Escape') setMenuOpen(false);
  });
}
