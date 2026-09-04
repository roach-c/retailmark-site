# Where these photographs came from — unresolved

> **Removed from the site on 2026-09-04.** The hero no longer uses them: it is
> a scrim over cycling retail interiors from Pexels now (`hero_photos.py`),
> which are licensed for commercial use. The `.webp` files are deleted rather
> than left in place, because an unreferenced file in this repo is still a file
> the web server hands out — and the licensing below was never resolved. This
> note and `photos.py` stay as the record; `git log` has the images if the
> question ever gets answered.

**Four of the original ten were dropped** — see `photos.py`'s SKIP list. The
Walmart welcome centre, which crops to a lone M in a strip. `images.jpeg`, a
596x335 source needing 4.5x enlargement. The Walmart rebrand article image at
3.8x. And the Shutterstock file, grainy at 2.2x with WALTON on the storefront
in it. `MAX_UPSCALE` refuses anything past 2.6x, because beyond that a strip
looks soft however good the composition is.

**Two Walmart images remain** — the Flintco fitness centre and the campus
rendering — on a site that carries no Walmart branding by design. Worth a
decision alongside the licensing one.

These were built into the hero slideshow from `~/Desktop/RetailMark Photos`.
**They are not cleared for a public site**, and this file exists so that is not
forgotten. Nine of the ten carry no camera metadata; the filenames are what
they are.

| file | what the name says |
|---|---|
| `shutterstock-1366855787` | a Shutterstock asset ID. Shutterstock watermarks previews and pursues unlicensed commercial use. |
| `sunrise-on-the-bentonville-arkansas-water-tower-gregory-ballos` | credited to Gregory Ballos, a working photographer who sells this as a print. |
| `00biz-walmart-cool-rebrand-01-tfwz-articleLarge` | `articleLarge` and that slug shape are New York Times image naming. |
| `27352_Bentonville_356w_preview-…` | "preview" is what an asset library calls its unlicensed copy. |
| `images.jpeg` | the filename Google Images gives a download. |
| `Flintco_Walmart-Fitness-Center_Exterior7` | Flintco is the contractor. Their project photograph. |
| `Rendering_of_wide_view_of_office_spaces` | an architectural rendering, Photoshop metadata, no camera. |
| `Welcome-Center-Exterior-2` | Walmart's own visitor centre. |
| `Central_Avenue_at_night` | the only one with camera EXIF (FujiFilm S1800, Picasa). Reads as a Wikimedia upload, which usually means CC BY-SA — usable **with** attribution. |
| `1940-1532185170` | 4608×2592, no metadata. Unknown. |

Two separate problems:

1. **Licensing.** Putting these on a commercial site is infringement. It is the
   client's business and the agency's name on the footer.
2. **Walmart marks.** Three of them are Walmart property or Walmart branded.
   This site has deliberately carried no Walmart branding since it was built —
   RetailMark is a brokerage, not an affiliate, and neither competitor shows
   Walmart imagery either.

## What actually works here

- Photographs Justin or the team take themselves. Phone photos are fine. The
  panel is 4:5 and centre-crops, so anything roughly upright works.
- A paid stock licence. Adobe Stock or Shutterstock, a few dollars an image,
  and the receipt lives with the site.
- Unsplash or Pexels, which are free for commercial use. Weaker, because
  generic stock undercuts a page whose whole claim is local knowledge.

Drop replacements into the source folder and run:

    python3 photos.py "~/Desktop/RetailMark Photos"

Nothing else changes — the page reads whatever is in `assets/bentonville/`.
