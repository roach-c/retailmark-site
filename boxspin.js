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

  // the hero's lighting, so the box reads as the same object under the same
  // light rather than a differently lit twin
  scene.add(new THREE.AmbientLight(0xffffff, 0.55));
  const key = new THREE.DirectionalLight(0xffffff, 1.15);
  key.position.set(5, 8, 6);
  scene.add(key);
  const warm = new THREE.PointLight(GOLD, 8, 10);
  warm.position.set(-2.2, 1.4, 2.2);
  scene.add(warm);

  const { mesh: box } = makeBox(THREE);
  scene.add(box);

  /* Framing. A turning box is widest on its diagonal, not on its face, so the
     fit uses the corner radius — otherwise it fits at rest and clips its own
     edges a second later, halfway through the turn. */
  const EYE = new THREE.Vector3(0.34, 0.42, 1).normalize();
  const MARGIN = 1.28;                       // air around it; it is not a portrait

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

  const CYCLE = 5.0;      // one turn every five seconds
  const TURN = 1.9;       // of which this much is actually turning
  const smooth = (v) => v * v * (3 - 2 * v);

  let running = true;
  new IntersectionObserver((es) => { running = es[0].isIntersecting; },
    { threshold: 0.05 }).observe(canvas);

  function frame(ms) {
    requestAnimationFrame(frame);
    if (!running) return;
    resize();

    const t = (ms / 1000) % CYCLE;
    const p = t < TURN ? smooth(t / TURN) : 1;
    box.rotation.y = p * Math.PI * 2;
    // a breath of drift so the resting pose is not dead still
    box.rotation.x = Math.sin(ms / 3400) * 0.045;

    renderer.render(scene, camera);
  }
  requestAnimationFrame(frame);
}
