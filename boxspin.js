/* RetailMark brand band: the hero's box, turning.

   Literally the same box — box.js is the one definition, imported here and by
   hero3d.js, so it cannot drift into being a near-copy.

   It rests facing the viewer with its label readable, then makes one smooth
   turn on the vertical axis, once every five seconds. Resting is the point:
   a box spinning without pause is wallpaper, and the label — the thing that
   makes it a product rather than a cube — would only be legible in passing.

   Degrades like the hero: no WebGL, a failed module load, or reduced motion
   and the band is simply the monogram and the line. */
import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.169.0/build/three.module.js";
import { makeBox, GOLD, SIZE } from "./box.js";

const canvas = document.getElementById("boxspin");
if (canvas && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(30, 1.5, 0.1, 40);

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

  /* Brighter than the hero's rig, on purpose. The box is the same object with
     the same material — but the hero sits on cream, which throws light back at
     it, while this one sits on near-black that returns nothing. Under the
     hero's lighting it measured (168,132,12) against the brand's (232,185,35):
     the same gold, reading as olive. So the LIGHT is corrected here rather
     than the colour, which would have meant two different golds on one page. */
  scene.add(new THREE.AmbientLight(0xffffff, 1.4));
  const key = new THREE.DirectionalLight(0xffffff, 1.7);
  key.position.set(5, 8, 6);
  scene.add(key);
  const fill = new THREE.DirectionalLight(0xffffff, 0.7);
  fill.position.set(-4, 1, 3);          // stands in for the bounce the cream gives the hero
  scene.add(fill);
  const warm = new THREE.PointLight(GOLD, 12, 10);
  warm.position.set(-2.2, 1.4, 2.2);
  scene.add(warm);

  const { mesh: box } = makeBox(THREE);
  scene.add(box);

  /* Framing. A turning box is widest on its diagonal, not on its face, so the
     fit uses the corner radius — otherwise it fits at rest and clips its own
     edges a second later, halfway through the turn. */
  // Elevation ~9 degrees, not ~22. Looking down on a product reads as looking
  // down on it; near eye level reads as the thing sitting on a shelf in front
  // of you, which is the whole idea of the site.
  const EYE = new THREE.Vector3(0.34, 0.16, 1).normalize();
  const MARGIN = 1.06;                       // just enough air that no angle touches an edge

  /* The volume the box sweeps as it turns: a cylinder of the corner radius,
     the box's own height. Fitting the box at rest is not enough — it is widest
     on its diagonal, so it fits facing you and clips its own corners a second
     later. Fitting the swept box means it never touches an edge at any angle. */
  const R = Math.hypot(SIZE.w, SIZE.d) / 2;
  const CORNERS = [];
  for (const x of [-R, R])
    for (const y of [-SIZE.h / 2, SIZE.h / 2])
      for (const z of [-R, R])
        CORNERS.push(new THREE.Vector3(x, y, z));

  const FWD = EYE.clone().negate();
  const RIGHT = new THREE.Vector3().crossVectors(FWD, new THREE.Vector3(0, 1, 0)).normalize();
  const UP = new THREE.Vector3().crossVectors(RIGHT, FWD).normalize();

  function fit() {
    const tanV = Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2);
    const tanH = tanV * camera.aspect;
    let d = 0;
    for (const c of CORNERS) {
      const along = c.dot(EYE);
      d = Math.max(d, Math.abs(c.dot(RIGHT)) / tanH + along,
                      Math.abs(c.dot(UP)) / tanV + along);
    }
    camera.position.copy(EYE).multiplyScalar(d * MARGIN);
    camera.lookAt(0, 0, 0);
    camera.updateProjectionMatrix();
  }

  function resize() {
    const w = canvas.clientWidth, h = canvas.clientHeight;
    if (!w || !h) return;
    const px = renderer.getPixelRatio();
    if (canvas.width !== Math.floor(w * px) || canvas.height !== Math.floor(h * px)) {
      renderer.setSize(w, h, false);
      camera.aspect = w / h;
      fit();
    }
  }

  /* resize() first, not fit(). fit() alone runs against the camera's
     constructor aspect, so the very first painted frame is composed for a
     canvas shape that does not exist — one frame of the object oversized and
     clipped before it snaps right. Measured: frame 0 clipped, every frame
     after was clean. */
  resize();
  fit();

  const CYCLE = 6.0;      // one turn every five seconds
  const TURN = 2.28;       // of which this much is actually turning
  const TAU = Math.PI * 2;
  const smooth = (v) => v * v * (3 - 2 * v);
  const cyclePos = (t) => (t < TURN ? smooth(t / TURN) : 1) * TAU;

  let running = true;
  new IntersectionObserver((es) => { running = es[0].isIntersecting; },
    { threshold: 0.05 }).observe(canvas);

  /* ---- turning it yourself ---------------------------------------------
     Four states, and the last one is what stops it feeling abandoned: drag it
     and it follows the pointer, let go and it coasts, and once the coast dies
     it eases back to facing you before the automatic turn takes over again.
     Without that settle it would resume its cycle from whatever arbitrary
     angle you left it at, label pointing into the void.

     The auto turn is INTEGRATED rather than assigned. Setting the angle from
     the clock each frame would snap the box back to wherever the cycle
     happened to be the moment you released it. Adding the cycle's delta means
     it picks up from where you actually left it. */
  let mode = 'auto';                 // auto | drag | coast | settle
  let angle = 0, vel = 0, last = 0, prevPos = 0, settleFrom = 0, settleT = 0;
  let drag = null;

  function nearestFront(a) { return Math.round(a / TAU) * TAU; }

  canvas.addEventListener('pointerdown', (e) => {
    if (e.button !== 0) return;
    e.preventDefault();
    canvas.setPointerCapture(e.pointerId);
    canvas.classList.add('is-grabbed');
    drag = { x: e.clientX, t: performance.now() };
    mode = 'drag';
    vel = 0;
  });

  canvas.addEventListener('pointermove', (e) => {
    if (!drag) return;
    const now = performance.now();
    const dx = e.clientX - drag.x;
    const dt = Math.max((now - drag.t) / 1000, 0.001);
    const d = dx * 0.011;            // pixels to radians
    angle += d;
    vel = d / dt;
    drag.x = e.clientX; drag.t = now;
  });

  function release(e) {
    if (!drag) return;
    drag = null;
    canvas.classList.remove('is-grabbed');
    try { canvas.releasePointerCapture(e.pointerId); } catch (_) {}
    mode = 'coast';
  }
  canvas.addEventListener('pointerup', release);
  canvas.addEventListener('pointercancel', release);

  function frame(ms) {
    requestAnimationFrame(frame);
    if (!running) { last = ms; return; }
    resize();

    const dt = last ? Math.min((ms - last) / 1000, 0.05) : 0;
    last = ms;

    const pos = cyclePos((ms / 1000) % CYCLE);
    const step = pos - prevPos;
    prevPos = pos;

    if (mode === 'auto') {
      // wrapping the cycle gives one big negative step; ignore it
      angle += step > 0 ? step : 0;
    } else if (mode === 'coast') {
      angle += vel * dt;
      vel *= Math.pow(0.06, dt / 1.2);            // ~94% shed per second
      if (Math.abs(vel) < 0.25) { mode = 'settle'; settleFrom = angle; settleT = 0; }
    } else if (mode === 'settle') {
      settleT = Math.min(settleT + dt / 0.84, 1);
      angle = settleFrom + (nearestFront(settleFrom) - settleFrom) * smooth(settleT);
      if (settleT >= 1) { angle = nearestFront(angle); mode = 'auto'; }
    }

    box.rotation.y = angle;
    // a breath of drift so the resting pose is not dead still
    box.rotation.x = Math.sin(ms / 4080) * 0.04;

    renderer.render(scene, camera);
  }
  requestAnimationFrame(frame);
}
