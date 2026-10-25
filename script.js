const root = document.documentElement;
const modeButton = document.querySelector('[data-mode-toggle]');
const modeLabel = document.querySelector('[data-mode-label]');
const themeColor = document.querySelector('meta[name="theme-color"]');
const siteFooter = document.querySelector('.site-footer');
const year = document.querySelector('[data-year]');
const heroTitle = document.querySelector('#hero-title');
const heroNames = heroTitle ? [...heroTitle.querySelectorAll('.hero-name')] : [];
const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
let footerInView = false;

const createHeroLetterMotion = () => {
  if (!heroTitle || heroNames.length === 0 || reduceMotion.matches) return;

  const letters = [];

  heroNames.forEach((name) => {
    [...name.children].forEach((part) => {
      const text = part.textContent;
      part.textContent = '';

      [...text].forEach((character) => {
        const letter = document.createElement('span');
        letter.className = 'hero-letter';
        letter.textContent = character;
        part.append(letter);
        letters.push({
          element: letter,
          x: 0,
          y: 0,
          velocityX: 0,
          velocityY: 0
        });
      });
    });
  });

  heroTitle.classList.add('hero-title-interactive');

  const pointer = {
    active: false,
    x: 0,
    y: 0
  };
  let motionFrame = 0;

  const requestMotionFrame = () => {
    if (motionFrame) return;
    motionFrame = requestAnimationFrame(updateLetters);
  };

  const updateLetters = () => {
    motionFrame = 0;
    let moving = false;
    const repulsionRadius = Math.min(Math.max(window.innerWidth * 0.12, 96), 168);

    letters.forEach((letter) => {
      const rect = letter.element.getBoundingClientRect();
      const centerX = rect.left + (rect.width / 2) - letter.x;
      const centerY = rect.top + (rect.height / 2) - letter.y;
      const distanceX = centerX - pointer.x;
      const distanceY = centerY - pointer.y;
      const distance = Math.hypot(distanceX, distanceY) || 1;
      const proximity = pointer.active
        ? Math.max(0, 1 - (distance / repulsionRadius))
        : 0;
      const displacement = proximity * proximity * 22;
      const targetX = (distanceX / distance) * displacement;
      const targetY = (distanceY / distance) * displacement;

      letter.velocityX = (letter.velocityX + ((targetX - letter.x) * 0.14)) * 0.76;
      letter.velocityY = (letter.velocityY + ((targetY - letter.y) * 0.14)) * 0.76;
      letter.x += letter.velocityX;
      letter.y += letter.velocityY;

      if (
        Math.abs(letter.x - targetX) > 0.02
        || Math.abs(letter.y - targetY) > 0.02
        || Math.abs(letter.velocityX) > 0.02
        || Math.abs(letter.velocityY) > 0.02
      ) {
        moving = true;
      }

      letter.element.style.setProperty('--letter-x', `${letter.x.toFixed(2)}px`);
      letter.element.style.setProperty('--letter-y', `${letter.y.toFixed(2)}px`);
    });

    if (moving) requestMotionFrame();
  };

  heroTitle.addEventListener('pointermove', (event) => {
    if (event.pointerType === 'touch') return;
    pointer.active = true;
    pointer.x = event.clientX;
    pointer.y = event.clientY;
    requestMotionFrame();
  }, { passive: true });

  heroTitle.addEventListener('pointerleave', () => {
    pointer.active = false;
    requestMotionFrame();
  }, { passive: true });

  heroTitle.addEventListener('pointerdown', (event) => {
    const titleRect = heroTitle.getBoundingClientRect();
    const reach = Math.hypot(titleRect.width, titleRect.height) || 1;

    letters.forEach((letter, index) => {
      const rect = letter.element.getBoundingClientRect();
      const centerX = rect.left + (rect.width / 2) - letter.x;
      const centerY = rect.top + (rect.height / 2) - letter.y;
      let distanceX = centerX - event.clientX;
      let distanceY = centerY - event.clientY;
      let distance = Math.hypot(distanceX, distanceY);

      if (distance < 1) {
        const angle = (index / letters.length) * Math.PI * 2;
        distanceX = Math.cos(angle);
        distanceY = Math.sin(angle);
        distance = 1;
      }

      const impulse = Math.max(2.5, 13 * (1 - Math.min(distance / reach, 0.82)));
      letter.velocityX += (distanceX / distance) * impulse;
      letter.velocityY += (distanceY / distance) * impulse;
    });

    requestMotionFrame();
  }, { passive: true });
};

createHeroLetterMotion();

document.querySelectorAll('a[target="_blank"]').forEach((link) => {
  const notice = 'abre nunha nova lapela';
  const accessibleLabel = link.getAttribute('aria-label');

  if (accessibleLabel) {
    link.setAttribute('aria-label', `${accessibleLabel}, ${notice}`);
    return;
  }

  const screenReaderNotice = document.createElement('span');
  screenReaderNotice.className = 'sr-only';
  screenReaderNotice.textContent = `, ${notice}`;
  link.append(screenReaderNotice);
});

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

const updateThemeColor = () => {
  if (!themeColor) return;

  const pageColor = root.dataset.mode === 'calm' ? '#f7f7f3' : '#c7ff00';
  themeColor.setAttribute('content', footerInView ? '#000000' : pageColor);
};

const updateMode = () => {
  const calm = root.dataset.mode === 'calm';
  modeButton.setAttribute('aria-pressed', String(calm));
  modeButton.setAttribute('aria-label', calm ? 'Activar o modo flúor' : 'Activar o modo calma');
  modeLabel.textContent = calm ? 'CALMA → FLÚOR' : 'FLÚOR → CALMA';
  updateThemeColor();
};

updateMode();

if (siteFooter && 'IntersectionObserver' in window) {
  const footerThemeObserver = new IntersectionObserver((entries) => {
    footerInView = entries.some((entry) => entry.isIntersecting);
    updateThemeColor();
  }, {
    threshold: 0.01
  });

  footerThemeObserver.observe(siteFooter);
}

if (year) {
  year.textContent = new Date().getFullYear();
}

const emailAction = document.querySelector('[data-email-action]');
const contactWorker = 'https://contacto-aleatorio.miguel-guisantes.workers.dev';
const instapaperLink = document.querySelector('[data-instapaper-link]');
const instapaperTitle = document.querySelector('[data-instapaper-title]');
const privacyToggle = document.querySelector('[data-privacy-toggle]');
const privacyPanel = document.querySelector('#privacidade');
const privacySymbol = document.querySelector('[data-privacy-symbol]');

const setPrivacyPanel = (open, { focus = false } = {}) => {
  if (!privacyToggle || !privacyPanel) return;

  privacyPanel.hidden = !open;
  privacyToggle.setAttribute('aria-expanded', String(open));
  if (privacySymbol) privacySymbol.textContent = open ? '−' : '+';

  if (open && focus) {
    privacyPanel.scrollIntoView({ block: 'start' });
    privacyPanel.querySelector('a, button')?.focus({ preventScroll: true });
  }
};

privacyToggle?.addEventListener('click', () => {
  setPrivacyPanel(privacyToggle.getAttribute('aria-expanded') !== 'true');
});

const openPrivacyFromHash = () => {
  if (window.location.hash !== '#privacidade' || !privacyPanel) return;

  setPrivacyPanel(true);
  requestAnimationFrame(() => privacyPanel.scrollIntoView({ block: 'start' }));
};

window.addEventListener('hashchange', openPrivacyFromHash);
openPrivacyFromHash();

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
        `Abrir o perfil público de Instapaper de Miguel. Último artigo que lle gustou: ${cleanTitle}, abre nunha nova lapela`
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
