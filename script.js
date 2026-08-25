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

    var BASE = 58;        // px/sec, the resting speed
    var MAX = 1400;       // however hard it is pushed, it stays watchable
    var EASE = 1.1;       // seconds to settle back toward BASE
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
