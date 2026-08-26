/* RetailMark brand band: the gold box opens and its products come out.

   Deliberately the SAME box that gets placed on the shelf in the hero, so the
   two animations read as one idea seen twice — the product arriving, then the
   product being what is inside. Everything is in the gold family on black; no
   second colour is introduced.

   Degrades the same way the hero does: no WebGL, a failed module load, or a
   reduced-motion setting and the band is simply the monogram and the line.

   No Walmart marks, same as everywhere else on this site. */
import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.169.0/build/three.module.js";

const canvas = document.getElementById("boxopen");
if (canvas && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
  const GOLD = 0xe8b923, GOLD_LIGHT = 0xf5d566, GOLD_DARK = 0xc79a15;
  const CARD = 0xb98f14;                    // the box itself, a shade down

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(34, 1.6, 0.1, 60);
  const EYE = new THREE.Vector3(3.1, 2.5, 4.6).normalize();

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

  scene.add(new THREE.AmbientLight(0xffffff, 0.5));
  const key = new THREE.DirectionalLight(0xffffff, 1.25);
  key.position.set(4, 7, 5);
  scene.add(key);
  // a warm bounce from below so the black band does not eat the underside
  const warm = new THREE.PointLight(GOLD, 14, 12);
  warm.position.set(-2, -1.4, 2.4);
  scene.add(warm);

  const rig = new THREE.Group();
  scene.add(rig);

  /* ---- the box -------------------------------------------------------
     Built as five thin panels rather than one solid box: the flaps open, and
     a solid box would still have a lid-coloured face sitting where the
     opening should be. Hollow means opening it actually reveals something. */
  const W = 1.5, Hh = 1.05, D = 1.5, T = 0.07;
  const shell = new THREE.MeshStandardMaterial({ color: CARD, roughness: .62, metalness: .18 });
  const inner = new THREE.MeshStandardMaterial({ color: GOLD_DARK, roughness: .8, metalness: .05 });

  const box = new THREE.Group();
  rig.add(box);

  const bottom = new THREE.Mesh(new THREE.BoxGeometry(W, T, D), inner);
  bottom.position.y = -Hh / 2;
  box.add(bottom);

  [[0, 0, D / 2], [0, 0, -D / 2]].forEach(([x, y, z]) => {
    const m = new THREE.Mesh(new THREE.BoxGeometry(W, Hh, T), shell);
    m.position.set(x, 0, z); box.add(m);
  });
  [[W / 2, 0, 0], [-W / 2, 0, 0]].forEach(([x, y, z]) => {
    const m = new THREE.Mesh(new THREE.BoxGeometry(T, Hh, D), shell);
    m.position.set(x, 0, z); box.add(m);
  });

  /* Four flaps, each on its own pivot at the top edge of its wall, so opening
     is a rotation about that hinge rather than a mesh being moved and rotated
     into roughly the right place. */
  const flaps = [];
  const FLAP = D / 2 - T;
  [
    { pos: [0, Hh / 2, D / 2], rot: 0,             size: [W, T, FLAP] },
    { pos: [0, Hh / 2, -D / 2], rot: Math.PI,      size: [W, T, FLAP] },
    { pos: [W / 2, Hh / 2, 0], rot: -Math.PI / 2,  size: [D, T, FLAP] },
    { pos: [-W / 2, Hh / 2, 0], rot: Math.PI / 2,  size: [D, T, FLAP] },
  ].forEach(({ pos, rot, size }) => {
    const pivot = new THREE.Object3D();
    pivot.position.set(pos[0], pos[1], pos[2]);
    pivot.rotation.y = rot;
    const m = new THREE.Mesh(new THREE.BoxGeometry(size[0], size[1], size[2]), shell);
    m.position.z = -size[2] / 2;             // hangs inward from the hinge
    pivot.add(m);
    box.add(pivot);
    flaps.push(pivot);
  });

  /* ---- what comes out ------------------------------------------------
     Assorted shapes so it reads as "products" rather than "more cubes", and a
     fixed pseudo-random sequence rather than Math.random so every loop is the
     same one — a shot that rearranges itself each time looks like a glitch. */
  let seed = 20260826;
  const rnd = () => (seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648;

  const shapes = [
    () => new THREE.BoxGeometry(.34, .44, .34),
    () => new THREE.CylinderGeometry(.19, .19, .46, 18),
    () => new THREE.SphereGeometry(.22, 20, 14),
    () => new THREE.BoxGeometry(.46, .3, .3),
    () => new THREE.ConeGeometry(.22, .46, 18),
  ];
  const tones = [GOLD, GOLD_LIGHT, GOLD_DARK];

  const items = [];
  for (let i = 0; i < 9; i++) {
    const mesh = new THREE.Mesh(
      shapes[i % shapes.length](),
      new THREE.MeshStandardMaterial({
        color: tones[i % tones.length], roughness: .34, metalness: .3,
        emissive: tones[i % tones.length], emissiveIntensity: .14,
        transparent: true,
      }));
    const a = (i / 9) * Math.PI * 2 + rnd() * .5;
    items.push({
      mesh,
      // where it ends up: a loose ring above the box, at mixed heights
      to: new THREE.Vector3(Math.cos(a) * (.72 + rnd() * .5),
                            .88 + rnd() * .72,
                            Math.sin(a) * (.72 + rnd() * .5)),
      spin: new THREE.Vector3(rnd() * 1.6 - .8, rnd() * 1.6 - .8, rnd() * 1.6 - .8),
      delay: i * 0.075,
    });
    rig.add(mesh);
  }

  /* ---- timing --------------------------------------------------------- */
  const IN = 1.0, OPEN = 0.8, OUT = 1.7, HOLD = 0.9, AWAY = 1.0;
  const CYCLE = IN + OPEN + OUT + HOLD + AWAY;

  const clamp01 = v => v < 0 ? 0 : v > 1 ? 1 : v;
  const easeOut = v => 1 - Math.pow(1 - v, 3);
  const smooth = v => v * v * (3 - 2 * v);

  let running = true;
  new IntersectionObserver(es => { running = es[0].isIntersecting; },
    { threshold: 0.05 }).observe(canvas);

  /* ---- framing --------------------------------------------------------
     Fitted to the whole SPREAD, not to the box. The box is small and the
     products end up well above and around it, so a camera framed on the box
     alone throws them off the top of the canvas — which is exactly what the
     first pass did. Same corner-fitting method as the hero: keep the angle,
     move the distance, check both fields of view so a short wide canvas and a
     tall narrow one are each handled. */
  const PAD = 0.3;                         // half an item, so nothing clips
  const CORNERS = [];
  items.forEach(it => {
    for (const dx of [-PAD, PAD])
      for (const dy of [-PAD, PAD])
        for (const dz of [-PAD, PAD])
          CORNERS.push(new THREE.Vector3(it.to.x + dx, it.to.y + dy, it.to.z + dz));
  });
  // and the box itself, flaps out at full stretch. The flaps are FLAP long and
  // swing just past vertical, so they add mostly height and only a little
  // spread — not the 0.9 in every direction the first pass assumed.
  for (const x of [-W / 2 - 0.1, W / 2 + 0.1])
    for (const y of [-Hh / 2 - 0.1, Hh / 2 + FLAP * 0.95])
      for (const z of [-D / 2 - 0.25, D / 2 + 0.25])
        CORNERS.push(new THREE.Vector3(x, y, z));

  const TARGET = new THREE.Box3().setFromPoints(CORNERS).getCenter(new THREE.Vector3());
  const FWD = EYE.clone().negate();
  const RIGHT = new THREE.Vector3().crossVectors(FWD, new THREE.Vector3(0, 1, 0)).normalize();
  const UP = new THREE.Vector3().crossVectors(RIGHT, FWD).normalize();
  const MARGIN = 1.06;

  function fit() {
    const tanV = Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2);
    const tanH = tanV * camera.aspect;

    /* Centre on what the CAMERA sees, not on the middle of the 3D bounds. The
       view is oblique, so the geometric centre does not land in the middle of
       the picture — the first pass framed it correctly and still left the box
       sitting left of centre with dead space beside it. Measuring the content
       along the camera's own right and up axes, then nudging the aim point by
       half that offset, puts it where it belongs. */
    let uMin = Infinity, uMax = -Infinity, vMin = Infinity, vMax = -Infinity;
    for (const c of CORNERS) {
      const rel = c.clone().sub(TARGET);
      const u = rel.dot(RIGHT), v = rel.dot(UP);
      if (u < uMin) uMin = u; if (u > uMax) uMax = u;
      if (v < vMin) vMin = v; if (v > vMax) vMax = v;
    }
    const aim = TARGET.clone()
      .addScaledVector(RIGHT, (uMin + uMax) / 2)
      .addScaledVector(UP, (vMin + vMax) / 2);

    let d = 0;
    for (const c of CORNERS) {
      const rel = c.clone().sub(aim);
      const along = rel.dot(EYE);
      d = Math.max(d, Math.abs(rel.dot(RIGHT)) / tanH + along,
                      Math.abs(rel.dot(UP)) / tanV + along);
    }
    camera.position.copy(aim).addScaledVector(EYE, d * MARGIN);
    camera.lookAt(aim);
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
  fit();

  function frame(ms) {
    requestAnimationFrame(frame);
    if (!running) return;
    resize();

    const t = (ms / 1000) % CYCLE;

    // 1. spins into existence
    const arrive = easeOut(clamp01(t / IN));
    const leave = smooth(clamp01((t - (CYCLE - AWAY)) / AWAY));
    const present = arrive * (1 - leave);
    box.scale.setScalar(present);
    rig.rotation.y = (1 - arrive) * Math.PI * 1.5 - 0.42 + Math.sin(ms / 4200) * .09;

    // 2. flaps fold open, and close again on the way out
    const open = smooth(clamp01((t - IN) / OPEN)) * (1 - leave);
    flaps.forEach((f, i) => { f.rotation.x = open * (Math.PI * 0.58 + (i % 2) * 0.05); });

    // 3. the products come out
    items.forEach((it, i) => {
      const p = smooth(clamp01((t - IN - OPEN * .55 - it.delay) / OUT));
      const gone = smooth(clamp01((t - (CYCLE - AWAY)) / AWAY));
      const s = p * (1 - gone);
      it.mesh.visible = s > 0.01;
      it.mesh.scale.setScalar(s);
      it.mesh.position.set(it.to.x * p, -0.25 + (it.to.y + 0.25) * p, it.to.z * p);
      it.mesh.rotation.set(it.spin.x * p * 3, it.spin.y * p * 3, it.spin.z * p * 3);
      it.mesh.material.opacity = s;
    });

    renderer.render(scene, camera);
  }
  requestAnimationFrame(frame);
}
