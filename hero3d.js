/* RetailMark hero: a retail shelf, with one product lifted off the floor and placed into an empty slot.
   No Walmart marks anywhere - RetailMark is a supplier consultancy, not an
   affiliate, so their branding must not appear.

   Degrades quietly: if WebGL is missing, the module fails to load, or the
   visitor prefers reduced motion, the hero simply renders without it. */
import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.169.0/build/three.module.js";
import { makeBox, GOLD as BOX_GOLD, CREAM as BOX_CREAM } from "./box.js";

const canvas = document.getElementById("hero3d");
if (canvas) {
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const GOLD = BOX_GOLD, CREAM = BOX_CREAM, WOOD = 0x2a2a30;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(30, 2, 0.1, 100);
  camera.position.set(7.6, 3.8, 13.5);
  camera.lookAt(0, 0.2, 0);

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));   // cap: 3x costs a lot for nothing

  scene.add(new THREE.AmbientLight(0xffffff, 0.55));
  const key = new THREE.DirectionalLight(0xffffff, 1.15);
  key.position.set(5, 8, 6);
  scene.add(key);
  const warm = new THREE.PointLight(GOLD, 26, 18);
  warm.position.set(-3.4, 2.2, 3.2);
  scene.add(warm);

  const group = new THREE.Group();
  group.scale.setScalar(0.74);
  // Was nudged +1.5 to clear the headline. The copy is its own left column now,
  // so the shelf is centred in its canvas and framed by fit() below instead.
  scene.add(group);

  const plank = new THREE.BoxGeometry(7.4, 0.16, 2.0);
  const plankMat = new THREE.MeshStandardMaterial({ color: WOOD, roughness: 0.85, metalness: 0.05 });
  const SHELF_Y = [-1.5, 0.15, 1.8];
  SHELF_Y.forEach((y) => {
    const s = new THREE.Mesh(plank, plankMat);
    s.position.set(0, y, 0);
    group.add(s);
  });
  [-3.7, 3.7].forEach((x) => {
    const post = new THREE.Mesh(new THREE.BoxGeometry(0.16, 4.2, 2.0), plankMat);
    post.position.set(x, 0.15, 0);
    group.add(post);
  });

  // Products. One slot on the middle shelf is deliberately left empty.
  const boxGeo = new THREE.BoxGeometry(0.72, 1.0, 0.72);
  const palette = [0x3c3c46, 0x4a4a56, 0x33333c, 0x565663];
  const EMPTY = { shelf: 1, slot: 2 };
  const SLOT_X = [-2.7, -1.35, 0, 1.35, 2.7];

  SHELF_Y.forEach((y, si) => {
    SLOT_X.forEach((x, qi) => {
      if (si === EMPTY.shelf && qi === EMPTY.slot) return;
      const m = new THREE.Mesh(boxGeo, new THREE.MeshStandardMaterial({
        color: palette[(si + qi) % palette.length], roughness: 0.7, metalness: 0.08,
      }));
      m.position.set(x, y + 0.58, 0);
      m.rotation.y = (qi - 2) * 0.03;
      group.add(m);
    });
  });

  // the one that arrives — from box.js, the same definition the brand band
  // turns, so the two can never drift apart
  const { mesh: hero, label } = makeBox(THREE);
  /* How the one that arrives arrives.

     It used to rise 3.6 units straight up from below, which meant it passed
     clean through two shelf planks on the way — a box travelling through solid
     wood, which is not what "getting placed on the shelf" looks like.

     A shelf is stocked from the front, and the geometry insists on it anyway:
     the plank above sits at 1.72 and the box's top at 1.23, so there is only
     0.49 of headroom. There is no room to come down from above. So it glides
     in over the lip of the plank and is set down into the slot. */
  const restX = SLOT_X[EMPTY.slot];
  const restY = SHELF_Y[EMPTY.shelf] + 0.58;
  const APPROACH_Z = 1.7;   // how far in front of the shelf face it starts. Kept
                            // modest on purpose: the fit() below has to frame
                            // this pose too, and every unit further forward is
                            // a smaller shelf for the whole rest of the cycle.
  const HOVER_Y = 0.3;      // rides this high while moving in; plank top is 0.23
                            // below the box's underside, so nothing intersects

  // Where it begins: sitting on the floor, in front of the unit. The posts run
  // down to -1.95, so that is the floor line; a box resting on it has its
  // centre half its own height above.
  const FLOOR_Y = -1.95 + 0.5;
  const LIFT_SPINS = 1.25;  // turns it makes on the way up

  hero.position.set(restX, restY, 0);
  group.add(hero);

  /* ------------------------------------------------------------------
     Framing.

     The camera used to sit at a fixed distance, which meant the shelf was
     only fully in frame at the one window size it was tuned for. On a wide
     monitor the right-hand end ran off the edge of the screen.

     So: measure the shelf once, then pull the camera back along its own
     sight-line until the whole thing fits the canvas — checking the
     horizontal AND vertical field of view, since a tall narrow canvas runs
     out of width first and a short wide one runs out of height. The angle
     never changes, only the distance, so the shot looks identical and simply
     stops being cropped.
     ------------------------------------------------------------------ */
  const TARGET = new THREE.Vector3(0, 0.2, 0);
  const DIR = camera.position.clone().sub(TARGET).normalize();
  const MARGIN = 1.04;          // a little air, so it never kisses the edge

  // Measured across the whole of the idle rotation, not at one angle. The
  // group swings between -0.29 and -0.15 radians, and a shelf measured square
  // on is narrower than the same shelf turned: fit the resting pose and the
  // corners slide out of frame a few seconds later.
  //
  // Measured with the arriving box at both ends of its travel too, since out in
  // front of the shelf it is closer to the camera and therefore larger on
  // screen than it will ever be once it has landed.
  const SWING = [-0.29, -0.22, -0.15];
  const POSES = [
    { at: new THREE.Vector3(restX, restY, 0), spin: 0 },                    // landed
    { at: new THREE.Vector3(restX, restY + HOVER_Y, APPROACH_Z), spin: 0.45 }, // coming in
    // On the floor, mid-spin. Measured at 45 degrees because that is where a
    // turning cube is widest — its diagonal, not its face.
    { at: new THREE.Vector3(restX, FLOOR_Y, APPROACH_Z), spin: Math.PI / 4 },
  ];
  const bounds = new THREE.Box3();
  const restRotation = group.rotation.y;
  for (const r of SWING) {
    group.rotation.y = r;
    for (const pose of POSES) {
      hero.position.copy(pose.at);
      hero.rotation.y = pose.spin;
      group.updateMatrixWorld(true);
      bounds.union(new THREE.Box3().setFromObject(group));
    }
  }
  group.rotation.y = restRotation;
  hero.position.set(restX, restY, 0);
  hero.rotation.y = 0;
  group.updateMatrixWorld(true);

  // The eight corners, in the camera's own axes. Fitting the bounding *sphere*
  // is the one-liner version of this and it wastes a lot of room: a shelf is
  // wide, flat and shallow, so its sphere is far bigger than the shelf and the
  // render ends up small and marooned in the middle of its canvas. Fitting the
  // real corners lets it fill the space it has.
  const CORNERS = [];
  for (const x of [bounds.min.x, bounds.max.x])
    for (const y of [bounds.min.y, bounds.max.y])
      for (const z of [bounds.min.z, bounds.max.z])
        CORNERS.push(new THREE.Vector3(x, y, z).sub(TARGET));

  const FWD = DIR.clone().negate();
  const RIGHT = new THREE.Vector3().crossVectors(FWD, new THREE.Vector3(0, 1, 0)).normalize();
  const UP = new THREE.Vector3().crossVectors(RIGHT, FWD).normalize();

  function fit() {
    const vFov = THREE.MathUtils.degToRad(camera.fov);
    const tanV = Math.tan(vFov / 2);
    const tanH = tanV * camera.aspect;

    // For a camera at TARGET + DIR*d, a corner sits at depth (d - rel·DIR) and
    // must satisfy |lateral| <= tan(fov/2) * depth. Solve each for d, keep the
    // largest, and every corner is inside the frustum.
    let d = 0;
    for (const rel of CORNERS) {
      const along = rel.dot(DIR);
      d = Math.max(d,
        Math.abs(rel.dot(RIGHT)) / tanH + along,
        Math.abs(rel.dot(UP)) / tanV + along);
    }

    camera.position.copy(TARGET).addScaledVector(DIR, d * MARGIN);
    camera.lookAt(TARGET);
    camera.updateProjectionMatrix();
  }

  function resize() {
    const w = canvas.clientWidth, h = canvas.clientHeight;
    if (!w || !h) return;
    if (canvas.width !== w || canvas.height !== h) {
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

  let running = true, t = 0;
  new IntersectionObserver((es) => { running = es[0].isIntersecting; },
    { threshold: 0.01 }).observe(canvas);

  /* Three beats, in this order, and the order is the whole point. Run them at
     once and it reads as a box being thrown at a shelf; run them in sequence
     and it reads as a product getting picked up off the floor and put away.

       1. LIFT   off the floor, turning, up to shelf height
       2. GLIDE  back over the lip of the plank and into the row
       3. DROP   set down into the slot, with a small rebound

     All of it happens at z = APPROACH_Z until beat 2, which is what keeps the
     box clear of the shelf: the planks end at z = 1.0 and the box's back face
     never comes closer than 1.34 until it is already above the plank. */
  const FADE_IN_T = 0.55;     // materialises on the floor
  const LIFT_T = 1.15;        // floor -> shelf height, spinning
  const GLIDE_T = 1.6;        // in over the plank — the slowest beat on purpose
  const DROP_T = 0.5;         // set down
  const HOLD_T = 2.4;         // sits there, done
  const FADE_OUT_T = 0.6;     // and fades off the shelf, leaving the slot empty
  const CYCLE = FADE_IN_T + LIFT_T + GLIDE_T + DROP_T + HOLD_T + FADE_OUT_T;
  const ARRIVE = FADE_IN_T + LIFT_T + GLIDE_T + DROP_T;

  const LABEL_OPACITY = label.material.opacity;

  const clamp01 = (v) => (v < 0 ? 0 : v > 1 ? 1 : v);

  function frame(ms) {
    requestAnimationFrame(frame);
    if (!running) return;
    resize();

    if (!reduced) {
      t = (ms / 1000) % CYCLE;

      const lift = clamp01((t - FADE_IN_T) / LIFT_T);
      const glide = clamp01((t - FADE_IN_T - LIFT_T) / GLIDE_T);
      const drop = clamp01((t - FADE_IN_T - LIFT_T - GLIDE_T) / DROP_T);

      const up = lift * lift * (3 - 2 * lift);                // eases both ends

      // Smootherstep, not a cubic ease-out. An ease-out leaves at full speed
      // and slows down, which is what made this beat read as a shove; easing
      // both ends means it takes up the slack first and arrives under control.
      const inward = glide * glide * glide * (glide * (glide * 6 - 15) + 10);

      const down = 1 - Math.pow(1 - drop, 2);                 // lands soft

      // a small rebound the instant it touches down, then nothing
      const landed = t - ARRIVE;
      const settle = drop >= 1
        ? Math.sin(landed * 7) * Math.exp(-landed * 3.4) * 0.035
        : 0;

      // Rises to hover height, then beat 3 takes the hover back off again.
      const hoverY = restY + HOVER_Y;
      hero.position.y = FLOOR_Y + (hoverY - FLOOR_Y) * up - HOVER_Y * down + settle;
      hero.position.z = APPROACH_Z * (1 - inward);

      // Spins on the way up and is left slightly turned; the glide squares it
      // to the shelf, so it is straight by the time it lands.
      hero.rotation.y = LIFT_SPINS * Math.PI * 2 * (1 - up) + 0.45 * (1 - inward);

      hero.material.emissiveIntensity = 0.16 + (1 - down) * 0.42;

      /* The loop closes with a dissolve rather than a cut. It fades off the
         shelf once it has sat there a while, and fades back in on the floor —
         so the reset is something you watch instead of a frame where the box
         is suddenly somewhere else. The slot is briefly empty again, which is
         the state the whole shot is about. */
      const fadeIn = clamp01(t / FADE_IN_T);
      const fadeOut = clamp01((t - (CYCLE - FADE_OUT_T)) / FADE_OUT_T);
      const opacity = Math.min(fadeIn, 1 - fadeOut);
      hero.material.opacity = opacity;
      // the label rides on the front face, so it has to go with it
      label.material.opacity = LABEL_OPACITY * opacity;
      hero.visible = opacity > 0.002;

      group.rotation.y = -0.22 + Math.sin(ms / 6000) * 0.07;
    } else {
      hero.position.set(restX, restY, 0);
      hero.rotation.y = 0;
      hero.visible = true;
      hero.material.opacity = 1;
      label.material.opacity = LABEL_OPACITY;
      group.rotation.y = -0.22;
    }
    renderer.render(scene, camera);
  }
  requestAnimationFrame(frame);
}
