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

if ('IntersectionObserver' in window) {
  const sectionObserver = new IntersectionObserver((entries) => {
    const visible = entries
      .filter((entry) => entry.isIntersecting)
      .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];

    if (!visible) return;

    navLinks.forEach((link) => {
      const current = link.getAttribute('href') === `#${visible.target.id}`;
      if (current) link.setAttribute('aria-current', 'true');
      else link.removeAttribute('aria-current');
    });
  }, {
    threshold: [0.18, 0.35, 0.6],
    rootMargin: '-18% 0px -60%'
  });

  sections.forEach((section) => sectionObserver.observe(section));
}
