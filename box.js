/* The gold product box.

   One definition, imported by both animations: the hero, where it is placed
   onto the shelf, and the brand band, where it turns. "The same box" is then
   true by construction rather than by two sets of numbers that happen to
   match today and quietly stop matching the first time one is edited.

   THREE is passed in rather than imported here so there is exactly one copy of
   the library on the page, whichever module loads first. */

export const GOLD = 0xe8b923;
export const CREAM = 0xfaf8f3;
export const SIZE = { w: 0.72, h: 1.0, d: 0.72 };

/** Returns { mesh, label }. The label is a child of the mesh, so it rides
 *  along with any transform applied to the box. */
export function makeBox(THREE) {
  const mesh = new THREE.Mesh(
    new THREE.BoxGeometry(SIZE.w, SIZE.h, SIZE.d),
    new THREE.MeshStandardMaterial({
      color: GOLD, roughness: 0.35, metalness: 0.25,
      emissive: GOLD, emissiveIntensity: 0.16,
      // the hero fades it off the shelf at the end of its loop
      transparent: true,
    }));

  const label = new THREE.Mesh(
    new THREE.PlaneGeometry(0.5, 0.16),
    new THREE.MeshBasicMaterial({ color: CREAM, transparent: true, opacity: 0.9 }));
  label.position.set(0, 0.1, SIZE.d / 2 + 0.01);
  mesh.add(label);

  return { mesh, label };
}
