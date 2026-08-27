const root = document.documentElement;
const modeButton = document.querySelector('[data-mode-toggle]');
const modeLabel = document.querySelector('[data-mode-label]');
const themeColor = document.querySelector('meta[name="theme-color"]');
const year = document.querySelector('[data-year]');

const updateMode = () => {
  const calm = root.dataset.mode === 'calm';
  modeButton.setAttribute('aria-pressed', String(calm));
  modeButton.setAttribute('aria-label', calm ? 'Activar o modo flúor' : 'Activar o modo calma');
  modeLabel.textContent = calm ? 'CALMA → FLÚOR' : 'FLÚOR → CALMA';
  themeColor.setAttribute('content', calm ? '#f7f7f3' : '#c7ff00');
};

updateMode();

if (year) {
  year.textContent = new Date().getFullYear();
}

modeButton.addEventListener('click', () => {
  root.dataset.mode = root.dataset.mode === 'calm' ? 'fluor' : 'calm';

  try {
    localStorage.setItem('site-mode', root.dataset.mode);
  } catch (error) {
    // O cambio segue activo durante esta visita.
  }

  updateMode();
});

const revealElements = document.querySelectorAll('.reveal');

if ('IntersectionObserver' in window) {
  const revealObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target);
      }
    });
  }, {
    threshold: 0.08,
    rootMargin: '0px 0px -30px'
  });

  revealElements.forEach((element) => revealObserver.observe(element));
} else {
  revealElements.forEach((element) => element.classList.add('is-visible'));
}

const navLinks = [...document.querySelectorAll('.site-nav a[href^="#"]')];
const sections = navLinks
  .map((link) => document.querySelector(link.getAttribute('href')))
  .filter(Boolean);
const siteHeader = document.querySelector('.site-header');

const updateActiveNav = () => {
  const headerHeight = siteHeader?.offsetHeight ?? 0;
  const marker = headerHeight + Math.min(window.innerHeight * 0.22, 170);
  let activeSection = null;

  sections.forEach((section) => {
    if (section.getBoundingClientRect().top <= marker) {
      activeSection = section;
    }
  });

  const atPageEnd = window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4;
  if (atPageEnd) activeSection = sections.at(-1) ?? activeSection;

  navLinks.forEach((link) => {
    const current = activeSection && link.getAttribute('href') === `#${activeSection.id}`;
    if (current) link.setAttribute('aria-current', 'true');
    else link.removeAttribute('aria-current');
  });
};

let navUpdateQueued = false;
const queueActiveNavUpdate = () => {
  if (navUpdateQueued) return;
  navUpdateQueued = true;

  requestAnimationFrame(() => {
    updateActiveNav();
    navUpdateQueued = false;
  });
};

window.addEventListener('scroll', queueActiveNavUpdate, { passive: true });
window.addEventListener('resize', queueActiveNavUpdate);
window.addEventListener('hashchange', queueActiveNavUpdate);
queueActiveNavUpdate();
