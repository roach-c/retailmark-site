document.getElementById('year').textContent = new Date().getFullYear();

const navToggle = document.getElementById('navToggle');
const mainNav = document.querySelector('.main-nav');
navToggle.addEventListener('click', () => {
  mainNav.classList.toggle('open');
  mainNav.style.display = mainNav.classList.contains('open') ? 'flex' : '';
});
mainNav.querySelectorAll('a').forEach((link) => {
  link.addEventListener('click', () => {
    mainNav.classList.remove('open');
    mainNav.style.display = '';
  });
});

// Subtle shadow on the sticky header once the page has scrolled.
const siteHeader = document.querySelector('.site-header');
const updateHeaderShadow = () => {
  siteHeader.classList.toggle('is-scrolled', window.scrollY > 8);
};
updateHeaderShadow();
window.addEventListener('scroll', updateHeaderShadow, { passive: true });

// Lightweight scroll-reveal: fade/rise sections and stagger the service
// cards as they enter the viewport. Purely cosmetic — no dependencies.
const revealTargets = [
  '.logos-strip',
  '.services',
  '.why-inner',
  '.partners',
  '.contact-inner',
].map((sel) => document.querySelector(sel)).filter(Boolean);

if ('IntersectionObserver' in window) {
  const revealObserver = new IntersectionObserver(
    (entries, observer) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('in-view');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.15, rootMargin: '0px 0px -40px 0px' }
  );

  revealTargets.forEach((el) => {
    el.classList.add('reveal');
    if (el.classList.contains('services')) el.classList.add('reveal-stagger');
    revealObserver.observe(el);
  });
} else {
  // No IntersectionObserver support: leave everything visible as-is.
}

// Interior pages share this file but have no contact form on them, so every
// lookup below has to survive not finding one. Without the guard the whole
// script throws here and the nav toggle above it silently stops working.
const form = document.getElementById('contactForm');
const note = document.getElementById('formNote');
if (form) form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(form).entries());
  const submitBtn = form.querySelector('button[type="submit"]');
  submitBtn.disabled = true;
  note.textContent = 'Sending...';

  try {
    const res = await fetch('/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Request failed');
    note.textContent = "Thanks — we'll follow up shortly to schedule your call.";
    form.reset();
  } catch (err) {
    note.textContent = "Something went wrong — please email info@retailmark.com directly.";
  } finally {
    submitBtn.disabled = false;
  }
});

/* ---------------------------------------------------------------------------
   Brand marquee.

   Rolls forever at a base speed and never pauses. You can push it: drag it, or
   swipe it sideways on a trackpad, and it speeds up, slows, or briefly runs
   backwards — then eases back to the base speed on its own. It always returns
   to the same constant roll, so there is no state anyone can leave it stuck in.

   Deliberately only HORIZONTAL input. Hijacking vertical wheel would mean the
   page stops scrolling whenever the pointer happens to cross this strip, which
   is the kind of clever that makes a site feel broken.
   --------------------------------------------------------------------------- */
(function () {
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)');

  document.querySelectorAll('[data-marquee]').forEach(function (marquee) {
    var track = marquee.querySelector('.marquee-track');
    var set = marquee.querySelector('.marquee-set');
    if (!track || !set || reduced.matches) return;

    marquee.classList.add('is-live');       // hands the transform to us

    var BASE = 48;        // px/sec, the resting speed
    var MAX = 1400;       // however hard it is pushed, it stays watchable
    var EASE = 1.32;       // seconds to settle back toward BASE
    var offset = 0, speed = BASE, last = 0, drag = null;

    function span() { return set.getBoundingClientRect().width; }

    function frame(now) {
      requestAnimationFrame(frame);
      var dt = last ? Math.min((now - last) / 1000, 0.05) : 0;
      last = now;

      if (drag) {
        // while held, the strip follows the pointer exactly
      } else {
        speed += (BASE - speed) * (1 - Math.exp(-dt / EASE));
        offset += speed * dt;
      }

      var w = span();
      if (w) offset = ((offset % w) + w) % w;   // wrap both directions
      track.style.transform = 'translateX(' + (-offset) + 'px)';
    }
    requestAnimationFrame(frame);

    /* ---- swipe sideways to push it ---- */
    marquee.addEventListener('wheel', function (e) {
      // deltaX is a deliberate sideways gesture; shift+wheel is the mouse
      // equivalent. Plain vertical scroll is left alone for the page.
      var dx = Math.abs(e.deltaX) > Math.abs(e.deltaY) ? e.deltaX
             : (e.shiftKey ? e.deltaY : 0);
      if (!dx) return;
      e.preventDefault();
      speed = Math.max(-MAX, Math.min(MAX, speed + dx * 1.6));
    }, { passive: false });

    /* ---- or grab it ---- */
    marquee.addEventListener('pointerdown', function (e) {
      if (e.button !== 0) return;
      marquee.setPointerCapture(e.pointerId);
      marquee.classList.add('is-dragging');
      drag = { x: e.clientX, t: performance.now(), v: 0 };
    });

    marquee.addEventListener('pointermove', function (e) {
      if (!drag) return;
      var dx = e.clientX - drag.x;
      var now = performance.now();
      var dt = Math.max((now - drag.t) / 1000, 0.001);
      offset -= dx;
      drag.v = -dx / dt;              // carried out of the drag as momentum
      drag.x = e.clientX;
      drag.t = now;
    });

    function release(e) {
      if (!drag) return;
      speed = Math.max(-MAX, Math.min(MAX, drag.v || BASE));
      drag = null;
      marquee.classList.remove('is-dragging');
      try { marquee.releasePointerCapture(e.pointerId); } catch (_) {}
    }
    marquee.addEventListener('pointerup', release);
    marquee.addEventListener('pointercancel', release);
  });
})();

/* ---------------------------------------------------------------------------
   Wordmark -> monogram.

   The wordmark starts centred in the band and travels left as it collapses,
   finishing as RM on the left gutter with the rest of the band free.

   The starting offset has to be measured rather than written into the CSS: it
   is (how much room is spare) / 2, and both the band's width and the
   wordmark's rendered width change with the viewport. It is expressed in SVG
   user units, because a CSS transform on an SVG child works in the local
   coordinate system — so it is divided by the scale the SVG is drawn at.
   --------------------------------------------------------------------------- */
(function () {
  var band = document.querySelector('.brandmark');
  var svg = band && band.querySelector('.rm');
  if (!band || !svg) return;

  var VIEWBOX = 434;    // the SVG's own width: the finished RM
  var FULL = 1470;      // where the wordmark actually ends, out past the box

  function measure() {
    var inner = band.querySelector('.brandmark-inner');
    var room = inner.getBoundingClientRect().width;
    var scale = svg.getBoundingClientRect().width / VIEWBOX;
    if (!scale) return;
    // spare room, halved, converted from pixels into user units
    var start = (room / scale - FULL) / 2;
    band.style.setProperty('--rm-x', Math.max(0, start).toFixed(1));
  }

  measure();
  window.addEventListener('resize', measure, { passive: true });

  if (!('IntersectionObserver' in window)) return;
  new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) {
        measure();                       // in case it resized while off screen
        band.classList.add('is-revealed');
      } else {
        band.classList.remove('is-revealed');   // resets it for the next pass
      }
    });
  }, { threshold: 0.55 }).observe(band);
})();

/* ---------------------------------------------------------------------------
   Scroll reveals.

   Each piece fades and lifts into place the first time it is scrolled to, then
   is left alone — the observer stops watching it. Re-animating on every pass
   reads as a page that cannot settle rather than as polish.

   The selector list mirrors the one in styles.css. CSS decides what starts
   hidden; this decides what gets watched. An element in one list and not the
   other either never appears or never moves, so keep them in step.
   --------------------------------------------------------------------------- */
(function () {
  if (!document.documentElement.classList.contains('js-reveal')) return;

  var GROUPS = [
    ['.hero-badge', '.hero h1', '.hero-sub', '.hero-cta'],
    ['.hero-stats > div'],
    ['.logos-label', '.marquee'],
    ['.services > .container > h2', '.services > .container > .section-sub'],
    ['.service-card'],
    ['.why-copy > *'],
    ['.why-card'],
    ['.partners > .container > h2', '.partners > .container > .section-sub', '.partner-row'],
    ['.contact-copy > *'],
    ['.page-hero .crumbs', '.page-hero h1', '.page-hero-sub'],
    ['.lex-group'],
    ['.glossary-cta > .container > *'],
    ['.site-footer .container > *']
  ];

  var STEP = 101;     // ms between neighbours in a group
  var CAP = 6;        // stop stacking delay past this, or late cards crawl in

  if (!('IntersectionObserver' in window)) {
    // no observer: show everything rather than leave the page half-blank
    document.documentElement.classList.remove('js-reveal');
    return;
  }

  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (!e.isIntersecting) return;
      e.target.classList.add('is-in');
      io.unobserve(e.target);          // first time only
    });
  }, {
    // a little early, so a section has started before it is fully in view
    rootMargin: '0px 0px -8% 0px',
    threshold: 0.08
  });

  GROUPS.forEach(function (group) {
    var n = 0;
    group.forEach(function (sel) {
      document.querySelectorAll(sel).forEach(function (el) {
        el.style.setProperty('--reveal-delay', Math.min(n, CAP) * STEP + 'ms');
        n++;
        io.observe(el);
      });
    });
  });

  /* ---- the contact card waits longer ----------------------------------
     The generic trigger is 8% of the element, which for a 581px form means it
     fires when 46px of it has cleared the fold — so a 2.4s animation is over
     before you have scrolled to the thing. This one needs a quarter of the
     card inside a viewport shortened by 25%, which lands when the card is
     genuinely on screen rather than merely beginning to exist.

     Both panels are driven off ONE trigger, the wrapper, rather than watched
     separately. They are different heights and sit at different offsets, so
     observed individually they would cross their own thresholds at different
     moments and the two halves of a converge would start apart. */
  var stack = document.querySelector('.contact-stack');
  if (stack) {
    var pair = stack.querySelectorAll('.contact-accent, .contact-form');
    var lateIO = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        pair.forEach(function (el) { el.classList.add('is-in'); });
        lateIO.unobserve(e.target);
      });
    }, { rootMargin: '0px 0px -25% 0px', threshold: 0.25 });
    lateIO.observe(stack);
  }

  /* A safety net for anything the observer never reports on — an element with
     no height at load, or a browser that misses one. A page that permanently
     withholds its own content because of an animation is worse than no
     animation.

     It only rescues what is ON SCREEN. Revealing everything on a timer looks
     like a fix but is its own bug: it fires the animations of sections nobody
     has scrolled to yet, so by the time you arrive they have already played.
     That is exactly what made the contact card seem to trigger early. Content
     that is off screen and hidden is not trapped — it is waiting. */
  var ALL = GROUPS.concat([['.contact-accent', '.contact-form']]);
  function rescueVisible() {
    var h = window.innerHeight || document.documentElement.clientHeight;
    ALL.forEach(function (group) {
      group.forEach(function (sel) {
        document.querySelectorAll(sel).forEach(function (el) {
          if (el.classList.contains('is-in')) return;
          var r = el.getBoundingClientRect();
          if (r.top < h && r.bottom > 0) { el.classList.add('is-in'); io.unobserve(el); }
        });
      });
    });
  }
  setTimeout(rescueVisible, 5000);
  // and again whenever scrolling stops, for anything scrolled past while stuck
  var idle;
  window.addEventListener('scroll', function () {
    clearTimeout(idle);
    idle = setTimeout(rescueVisible, 1200);
  }, { passive: true });
})();
