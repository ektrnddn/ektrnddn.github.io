# Working notes for this site

Read this before touching anything. It records the decisions Eka has made so they are
not re-litigated or drifted from.

## Voice and content

- Copy is Eka's own words. Use her exact wording when she gives it; never pad, never
  "improve" it into AI-sounding prose. Short, plain, a little dry.
- No hint texts ("scroll to…", "click to…"), no explanatory captions, no emoji.
- No numbering anywhere: no "01 / 05", no "[1]" on lists, no "6 papers" counts, no
  "01 · Dual AGN". Section heads are plain words. (The only exception is the
  "Earlier work" paragraph on /research/, whose [n] markers are citations linking to
  the papers under it.)
- Physics is capitalised in "Ph.D. candidate in Physics". LISA sentence reads
  "the progenitors of mergers that LISA will detect".
- Her name appears once per page (nav); the footer spells it in blocks, that's all.

## Type

Exactly two fonts, loaded from Google Fonts in `src/layouts/Base.astro`:

- **Geist** for everything readable. Tight tracking on headings (`letter-spacing: -.03em`),
  weights 400/500 only.
- **Geist Mono** for small labels only (`.mono`: 12px, muted): years, kinds, captions,
  the "Interactive" badge, the pixel-word footer captions.

Do not add a third face. The explorer's canvas text is also Geist (`F_SERIF` in
`dualagn-explorer/index.html` is set to the Geist stack on purpose).

## Colour

Monochrome. Tokens live in `src/styles/global.css`:

| token      | value     | use                                   |
|------------|-----------|---------------------------------------|
| `--paper`  | `#ffffff` | page                                  |
| `--ink`    | `#191919` | headings, drawings, primary links     |
| `--text`   | `#444444` | body                                  |
| `--muted`  | `#737373` | labels, captions                      |
| `--rule`   | `#ececec` | hairlines                             |
| `--rose`   | `#d98aa0` | the meadow flowers; the only colour   |

If something needs colour, use `--rose` and nothing else: exactly `#d98aa0`, no tints.
It is used for the flowers in the drawing, for the explorer's "Read the paper" button
(ink text on rose) and, in the movie, for black holes that are accreting (AGN light).
The old crimson `#8F1D28` is gone.

## Interactions that exist (keep them working)

- Home drawing (`src/components/Sketch.astro`, generated): stars are pulled toward the
  cursor like a black hole and fade at the horizon; a click on the sky sets them
  floating freely, another click calls them home; no constellation lines. Hovering the
  walker makes her raise binoculars. Drawing layers parallax with the cursor.
- Home, after the drawing: "See the research", then the film (`src/components/Movie.astro`)
  beside the three stages: Dual AGN (kpc), Binary (sub-pc), Merger (gravitational waves),
  each with its sentence and the projects on it (linked from `projects.yaml`). The stage on
  screen is lit and its hairline fills; a click on a stage plays its part. The film is one
  ~30 s take from far away, with no words: the merger, the two AGN lighting up in rose, one
  point once they are too close to tell apart, the light going out, gravitational-wave rings
  leaving the remnant, a faint light again. It plays while on screen (a click or the round
  button toggles). Then "See the publications", "About me".
- Floating star (facts panel) only on the home page; it is draggable.
- Research: vertical card stack; the Cosmic Pairs card opens the live explorer in the
  zoom overlay. Nav orb next to the name unfolds Email (copies) / GitHub / LinkedIn.
- Footer: contact row, then the block-letter name at the very bottom; the friend's
  sketch stands on the base bar of the last "I" of DADIANI, as tall as its stem, with
  "as drawn by a friend" and a curly arrow beside it.

## Where things live

- Content: `src/data/*.yaml` (loaded through `src/data/load.ts`). `[label](url)` in
  facts makes a link; `[[text]]` in the intro highlights.
- About and the talks on Publications mirror the CV (talks appear only on Publications). The CV source is the private Overleaf repo
  `ektrnddn/Ekaterine_Dadiani_CV` (`main.tex`); read it with
  `gh api repos/ektrnddn/Ekaterine_Dadiani_CV/contents/main.tex --jq .content | base64 -d`
  and update the YAML to match when asked. Entries not in the CV are dropped.
- The drawing is generated: edit `docs/scene/scene_gen.py` (SVG) or
  `docs/scene/build_sketch.py` (stars, interactions, CSS), then run
  `python3 docs/scene/scene_gen.py docs/scene && python3 docs/scene/build_sketch.py docs/scene src/components/Sketch.astro`.
  Never hand-edit `Sketch.astro`.
- The film is rendered from simulations in `docs/movie/` into `public/movie/` (`merger.mp4`,
  `merger.webm`, square 1080 px; `poster.jpg`; one 720 px clip per stage in `clips/`). The stage
  words, the projects under each and the second each stage starts: `src/data/movie.yaml`.
  Physics: `galaxies.py` is a self-consistent N-body merger (tree gravity, 638k particles, run to
  1.25 Gyr, ~1.5 h on the M4); `nucleus.py` sinks the pair by dynamical friction below the
  N-body's resolution; `waves.py` hardens the binary and times the merger; `story.py` ties them to
  N-body time (when each hole shines, where the nucleus is); `render.py` films it (camera and
  timing keys at its top). The fiducial pair is 1e8 + 5e7 Msun. The rings at the merger are drawn
  far larger than the real wavelength (tens of AU) so they show at galaxy scale. Each frame is
  exposed over sub-frames (motion blur, wider in the binary stage's time-lapse, where a frame
  spans ~4 Myr); without it the stars flicker from frame to frame.
  Rebuild (Python deps in `docs/movie/requirements.txt`, CACHE is any scratch folder, ~3 GB):
  `python3 docs/movie/galaxies.py CACHE/nbody`, then
  `python3 docs/movie/render.py CACHE CACHE --exposure && python3 docs/movie/render.py CACHE public/movie`.
  `--stills 3,12.5` renders single frames for checking.
- The explorer is its own repo (`../dualagn-explorer`, single `index.html`, GitHub
  Pages from `main`). Its styling matches this site: light by default, eye toggle,
  flat chips, no boxes.
- Deploy: push to `main` on `ektrnddn/ektrnddn.github.io`; GitHub Actions builds and
  publishes. The CV compile step needs the `CV_REPO_TOKEN` secret (not set yet).

## Checking work

Build with `npm run build`; serve `dist/` on :8792 (`.claude/launch.json`,
`dist-preview`, which is `astro preview`: it answers range requests, so the film can seek;
`python3 -m http.server` does not). Headless Chrome screenshots work with a wrapper page that iframes the
site and dispatches events; the in-app browser pane is usually hidden, so its animation
frames pause there.
