const root = document.documentElement;
const modeButton = document.querySelector('[data-mode-toggle]');
const modeLabel = document.querySelector('[data-mode-label]');
const themeColor = document.querySelector('meta[name="theme-color"]');
const year = document.querySelector('[data-year]');
const heroTitle = document.querySelector('#hero-title');
const heroNames = heroTitle ? [...heroTitle.querySelectorAll('.hero-name')] : [];

const fitHeroNames = () => {
  if (!heroTitle || heroNames.length === 0) return;

  const titleWidth = heroTitle.clientWidth;
  const stacked = getComputedStyle(heroNames[0].firstElementChild).display === 'block';
  const fillRatios = stacked ? [0.98, 0.995, 0.94] : [0.74, 0.96, 0.78];
  const heightLimit = window.innerHeight * (stacked ? 0.17 : 0.255);
  const widthFits = [];

  heroNames.forEach((name, index) => {
    const style = getComputedStyle(name);
    const currentSize = Number.parseFloat(style.fontSize);
    const paddingLeft = Number.parseFloat(style.paddingLeft) || 0;
    const textWidths = [...name.children].map((part) => {
      const range = document.createRange();
      range.selectNodeContents(part);
      return range.getBoundingClientRect().width;
    });
    const textWidth = stacked
      ? Math.max(...textWidths)
      : textWidths.reduce((total, width) => total + width, 0);

    if (!currentSize || !textWidth) return;

    const availableWidth = Math.max(titleWidth - paddingLeft - 2, 1);
    widthFits.push(currentSize * ((availableWidth * fillRatios[index]) / textWidth));
  });

  if (widthFits.length !== heroNames.length) return;

  const minimum = stacked ? 64 : 72;
  const maximum = stacked ? 156 : 272;
  const sharedSize = Math.min(Math.max(Math.min(...widthFits), minimum), heightLimit, maximum);

  heroNames.forEach((name) => {
    name.style.fontSize = `${sharedSize.toFixed(2)}px`;
  });
};

let heroFitQueued = false;
const queueHeroFit = () => {
  if (heroFitQueued) return;
  heroFitQueued = true;

  requestAnimationFrame(() => {
    fitHeroNames();
    heroFitQueued = false;
  });
};

queueHeroFit();
window.addEventListener('resize', queueHeroFit, { passive: true });

if (document.fonts?.ready) {
  document.fonts.ready.then(queueHeroFit);
}

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

const emailAction = document.querySelector('[data-email-action]');
const contactWorker = 'https://contacto-aleatorio.miguel-guisantes.workers.dev';
const instapaperLink = document.querySelector('[data-instapaper-link]');
const instapaperTitle = document.querySelector('[data-instapaper-title]');

if (instapaperLink && instapaperTitle) {
  fetch(`${contactWorker}/instapaper-latest`, {
    headers: { Accept: 'application/json' },
    cache: 'no-store'
  })
    .then((response) => {
      if (!response.ok) throw new Error('Non se puido consultar Instapaper');
      return response.json();
    })
    .then(({ title }) => {
      if (typeof title !== 'string' || title.trim() === '') return;

      const cleanTitle = title.trim();
      instapaperTitle.textContent = cleanTitle;
      instapaperLink.setAttribute(
        'aria-label',
        `Abrir o perfil público de Instapaper de Miguel. Último artigo que lle gustou: ${cleanTitle}`
      );
    })
    .catch(() => {
      // Mantense o último título comprobado incluído no HTML.
    });
}

const citationCounters = [...document.querySelectorAll('[data-citation-doi]')];

const citationLabel = (count) => `${count} ${count === 1 ? 'CITA' : 'CITAS'}`;

citationCounters.forEach(async (counter) => {
  const doi = counter.dataset.citationDoi;
  const countNode = counter.querySelector('[data-citation-count]');
  if (!doi || !countNode) return;

  try {
    const response = await fetch(`https://api.openalex.org/works/https://doi.org/${doi}`, {
      headers: { Accept: 'application/json' }
    });

    if (!response.ok) return;

    const work = await response.json();
    if (!Number.isInteger(work.cited_by_count) || work.cited_by_count < 0) return;

    countNode.textContent = citationLabel(work.cited_by_count);
    counter.dataset.citationStatus = 'live';
  } catch (error) {
    // Mantense a última cifra comprobada incluída no HTML.
  }
});

const fallbackContact = () => {
  const contactCodes = [
    109, 97, 105, 108, 116, 111, 58,
    111, 108, 97, 64, 109, 105, 103, 46, 109, 111, 122, 109, 97, 105, 108, 46, 99, 111, 109
  ];

  return String.fromCharCode(...contactCodes);
};

if (emailAction) {
  emailAction.addEventListener('click', async () => {
    if (emailAction.getAttribute('aria-busy') === 'true') return;

    emailAction.setAttribute('aria-busy', 'true');
    emailAction.disabled = true;

    try {
      const response = await fetch(contactWorker, {
        method: 'POST',
        headers: { Accept: 'application/json' },
        cache: 'no-store'
      });

      if (!response.ok) throw new Error('Non se puido obter unha máscara');

      const { address } = await response.json();

      if (!/^[a-z0-9]{12}@mig\.mozmail\.com$/.test(address)) {
        throw new Error('Formato de máscara incorrecto');
      }

      window.location.href = `mailto:${address}`;
    } catch (error) {
      window.location.href = fallbackContact();
    } finally {
      window.setTimeout(() => {
        emailAction.disabled = false;
        emailAction.removeAttribute('aria-busy');
      }, 600);
    }
  });
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
