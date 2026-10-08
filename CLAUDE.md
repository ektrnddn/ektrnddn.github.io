# Working notes for this site

Read this before touching anything. It records the decisions Eka has made so they are
not re-litigated or drifted from.

## Voice and content

- Copy is Eka's own words. Use her exact wording when she gives it; never pad, never
  "improve" it into AI-sounding prose. Short, plain, a little dry.
- No hint texts ("scroll to…", "click to…"), no explanatory captions, no emoji.
- No horizontal rules between items in lists; spacing, small mono labels and the vertical
  line do that work. Column titles are not needed when the columns explain themselves.
- No numbering anywhere: no "01 / 05", no "[1]" on lists, no "6 papers" counts, no
  "01 · Dual AGN". Section heads are plain words. (The only exception is the
  "Earlier work" paragraph on /research/, whose [n] markers are citations linking to
  the papers under it.)
- Physics is capitalised in "Ph.D. candidate in Physics". LISA sentence reads
  "the progenitors of mergers that LISA will detect".
- Her name appears once per page (nav); the footer spells it in blocks, that's all.

## Type

One font, Geist, loaded from Google Fonts in `src/layouts/Base.astro`. Weights 400/500 only.
Tracking: `-.03em` on titles, `-.02em` on subheads, `-.01em` on small text. The small grey
labels (`.label`: 12px, muted, tabular figures) are Geist too: years, kinds, scales, captions,
"Updated", the footer note. Geist Mono was dropped on 2026-10-08; she didn't like it.

Five sizes, tokens in `src/styles/global.css`; every `font-size` on the site is one of them:

| token    | size                      | use                                                    |
|----------|---------------------------|--------------------------------------------------------|
| `--t-xs` | 12px                      | labels                                                 |
| `--t-sm` | 14px                      | menu, footer, authors and venues, details, phone body  |
| `--t-md` | 16px                      | body, paper and project titles, links                  |
| `--t-lg` | clamp(19px, 1.65vw, 24px) | ledes: the home intro, the thesis, About bio, school names |
| `--t-xl` | clamp(28px, 3vw, 40px)    | page and section titles ("Research", "About me")       |

Line heights: 1.15 titles, 1.35 subheads and titles of items, 1.5 ledes and labels, 1.6 body.
Do not add a sixth size or a second face. The explorer's canvas text is also Geist (`F_SERIF` in
`dualagn-explorer/index.html` is set to the Geist stack on purpose).

## Colour

Monochrome: one grey ramp and the rose. Tokens live in `src/styles/global.css`; no other hex
values appear in the components (the drawing in `Sketch.astro` is generated with its own greys):

| token      | value     | use                                       |
|------------|-----------|-------------------------------------------|
| `--ink`    | `#191919` | headings, drawings, primary links         |
| `--text`   | `#444444` | body                                      |
| `--muted`  | `#737373` | labels, captions                          |
| `--soft`   | `#9b9b9b` | secondary lines and marks                 |
| `--faint`  | `#c8c8c8` | tertiary lines, leaders, small dots       |
| `--rule`   | `#ececec` | hairlines, the undrawn timeline           |
| `--wash`   | `#f4f4f4` | the faintest fill                         |
| `--paper`  | `#ffffff` | page                                      |
| `--rose`   | `#d98aa0` | the only colour                           |

Shadows are all `rgba(0,0,0,.35)`.

If something needs colour, use `--rose` and nothing else: exactly `#d98aa0`, no tints.
It is used for the flowers in the drawing, for the explorer's "Read the paper" button
(ink text on rose), in the movie for black holes that are accreting (AGN light), for the
"now" dot at the end of the About timeline, and in some flower heads of the sage drawn under
the About portrait.
The old crimson `#8F1D28` is gone.

## Interactions that exist (keep them working)

- Home drawing (`src/components/Sketch.astro`, generated): stars are pulled toward the
  cursor like a black hole and fade at the horizon; a click on the sky sets them
  floating freely, another click calls them home; no constellation lines. Hovering the
  walker makes her raise binoculars. Drawing layers parallax with the cursor.
- One page, except About: the home page is the drawing, then Research, then Publications, then
  "About me". The menu's Research and Publications go to those sections (`/#research`,
  `/#publications`); `/research` and `/publications` redirect there. Only About is its own page.
- Research (`src/components/ResearchFilm.astro`): Powers of Ten with the film. When "Research"
  reaches the top, everything stops there: the heading, the thesis title, the stage words and
  the film stay, and the scroll runs the film, forward going down and back going up (never on
  its own); the block is as tall as its content, so what follows comes right after. Beside the
  film the three stage names (the one on screen dark; a click jumps to it), under them only the
  stage's scale (the name is not repeated), then her words in `movie.yaml` and the papers on it,
  linked. Two papers carry a small thumbnail of their figure: Cosmic Pairs with "Interactive
  explorer" (the thumbnail opens the live explorer in the overlay, a new tab on phones) and the
  binaries search with "blrfit", its fitter on GitHub (the thumbnail opens the figure large). On
  phones the thumbnails give way to the links alone.
  Under the film a scale bar read off the film's camera (`src/data/film-fov.json`, written by
  `docs/movie/fov_table.py` from render.py's FOV_KEYS). The stages take half, a quarter and a
  quarter of the scroll. The film it scrubs is `public/movie/merger-scroll.mp4` (a keyframe every
  6 frames, so it seeks smoothly both ways), poster `scroll-start.jpg`. On phones the film sits
  above the words and the floating star steps aside while the film is on screen. Then "Earlier
  work" (its heading at the thesis title's size), whose [n] link to those papers in the
  publications just below and show the paper's title on hover.
- Publications (`src/components/PubTimeline.astro`, every paper and talk, never cut to a
  selection): newest year first, papers on the left (no bullets; her name bold in the authors),
  talks and schools on the right, and between them one line with the years on it. Phones: the
  line at the left, each year then its papers then its talks.
- Earlier versions of the research, kept for reference only: `_archive/research-cards/` (a hand
  of cards), `_archive/research-zoom/` (Powers of Ten drawn on a canvas),
  `_archive/research-constellation/`, `_archive/research-v2/`, `_archive/research-v3/` (results
  first, rejected as feeling generated), and `_archive/home-film-loop/` (the film looping
  beside its stages).
  Nav orb next to the name unfolds Email (copies) / GitHub / LinkedIn.
- About: the title, the bio (its second paragraph, the earlier life, one step smaller at the
  body size), Advisors / Collaborations / Based in (label on the left, answer on the right),
  then the CV button. Beside them her portrait, the full width of its column: black and
  white, its sky cut away so the tower, the rooftops and her hair meet the page, its sides
  fading into the paper and its bottom a straight edge, just under the last fact; above, it
  reaches up beside the title. No effect on the photo itself. Under its edge the photo's
  sage carries on in pen: each stem continues where a real stem leaves the photo and trails
  off on its own (nothing meets at a point, no ground), with sprigs and looping flower heads,
  some rose, beside the frame. When the page opens it is drawn stroke by stroke at a pen's
  pace, about 4.6 s. The photo comes from `_archive/photos/portrait-original.jpg` (not
  committed) through `docs/photo/cutout.py`; the drawing is `docs/photo/meadow.py`, which
  writes `src/components/PortraitMeadow.astro` with each stroke's delay and duration. Then the
  skills (same label-left form, no rules), then the timeline
  (`src/components/Timeline.astro`, data in `src/data/timeline.yaml`). Three columns, with no
  titles over them: education in general (the schools, big, a ring on the line; collaborations
  joined and schools and trainings, smaller, each a bar beside the line as long as it lasted,
  not joined to it, as in the second column: ink for collaborations, grey for trainings); what
  mattered most (research, projects,
  programmes), each with a bar as long as it lasted and the papers it led to beneath it; the
  small things along the way (prizes led by the place, talks, juries, small schools). One
  time scale for all three columns: a date sits at the same height across the page, and
  wherever a column needs room, time stretches there for every column. A line on the far left
  draws itself on scroll (its tip sits at 85% of the window height); whatever it hasn't
  reached yet waits blurred and faint, and comes into focus as it passes. No year ruler:
  every item carries its own date. Phones get one column in date order.
- Footer: contact row; on the home page only, the block-letter name at the very bottom; the friend's
  sketch (with a small mouse by the cat's paw, added in the same line) stands on the base bar
  of the last "I" of DADIANI, as tall as its stem, with "as drawn by a friend" and a curly
  arrow beside it.

## Where things live

- Content: `src/data/*.yaml` (loaded through `src/data/load.ts`). `[label](url)` in
  facts makes a link; `[[text]]` in the intro highlights.
- The talks in the publications and the skills on About mirror the CV. The About timeline mirrors it
  too but also holds things only in her older CVs (2016-2024): olympiads, hackathons, the
  Perimeter program, juries; dates marked `?` in `timeline.yaml` are guesses. The CV source is the private Overleaf repo
  `ektrnddn/Ekaterine_Dadiani_CV` (`main.tex`); read it with
  `gh api repos/ektrnddn/Ekaterine_Dadiani_CV/contents/main.tex --jq .content | base64 -d`
  and update the YAML to match when asked. Outside the timeline, entries not in the CV are dropped.
- The drawing is generated: edit `docs/scene/scene_gen.py` (SVG) or
  `docs/scene/build_sketch.py` (stars, interactions, CSS), then run
  `python3 docs/scene/scene_gen.py docs/scene && python3 docs/scene/build_sketch.py docs/scene src/components/Sketch.astro`.
  Never hand-edit `Sketch.astro`.
- The film is rendered from simulations in `docs/movie/` into `public/movie/` (`merger.mp4`,
  `merger.webm`, square 1080 px; `poster.jpg`; one 720 px clip per stage in `clips/`; and
  `merger-scroll.mp4` with `scroll-start.jpg`, which the home page scrolls through). The stage
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
