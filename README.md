# ektrnddn.github.io

Personal website of Ekaterine Dadiani: research, publications, talks and CV in one place.
Live at https://ektrnddn.github.io once the repository is published to GitHub.

## How it fits together

```
Overleaf  ──sync──▶  ektrnddn/Ekaterine_Dadiani_CV (private, LaTeX)
                              │  push → repository_dispatch "cv-updated"
                              ▼
                     ektrnddn/ektrnddn.github.io (this repo)
                       GitHub Action: compile CV → public/cv/*.pdf
                                      build Astro → deploy to Pages
                              │
                              ├── embeds  ektrnddn/dualagn-explorer  (public, its own Pages URL)
                              └── links   data.desi.lbl.gov/…/mbhb_offsets  (DESI members only)
```

- **CV.** The LaTeX source stays in its own private repo, kept in sync by Overleaf.
  The deploy workflow checks that repo out with a read-only token, compiles it, and
  ships the PDF at `/cv/Ekaterine_Dadiani_CV.pdf` together with the source's last commit
  date. The About page ends with the download button; `/cv` redirects there. A committed copy of the PDF in `public/cv/` is the fallback until the token is set.
  Setup: see "One-time setup" below.
- **Dual AGN explorer.** Stays in `ektrnddn/dualagn-explorer` so its URL keeps working in
  the paper. The research page for the DESI census embeds it in an iframe and links to
  the full-screen version.
- **DESI results page.** Behind the collaboration login, so the site links to it and marks
  it "DESI members". A public copy can be dropped into `public/` when the paper is out.

## Editing content

Everything shown on the site comes from plain files, no code changes needed:

| What                    | Where                              |
| ----------------------- | ---------------------------------- |
| Name, bio, links, skills, home intro | `src/data/profile.yaml` |
| Home page facts         | `src/data/facts.yaml`              |
| Mountain drawing        | `src/components/Sketch.astro` (ridge paths, meadow, figure; moves with the cursor) |
| Film photos on the home page | `src/data/photos.yaml` + files in `public/photos/` |
| Publications            | `src/data/publications.yaml`       |
| Talks and schools       | `src/data/talks.yaml`              |
| Education               | `src/data/education.yaml`          |
| Grants and fellowships  | `src/data/grants.yaml`             |
| Experience              | `src/data/experience.yaml`         |
| Awards                  | `src/data/awards.yaml`             |
| Research projects       | `src/data/projects.yaml` (title, figure, paper link, or a status line) |
| Figures                 | `public/figures/`                  |

Add a paper: append an entry to `publications.yaml` with an `arxiv` or `doi`; set
`selected: true` to feature it on the home page. Add a research project: append an entry
to `projects.yaml` with a title, a figure in `public/figures/` and the paper link, or
just a `status` line while it is in progress.

## Local development

```bash
npm install
npm run dev        # http://localhost:4321
npm run build      # static output in dist/
```

## One-time setup on GitHub

1. Create the repository `ektrnddn/ektrnddn.github.io` (public) and push `main`.
2. Repository → Settings → Pages → Source: **GitHub Actions**.
3. Create a fine-grained personal access token with **Contents: read** on
   `Ekaterine_Dadiani_CV`, and add it to this repo as the secret `CV_REPO_TOKEN`.
4. Optional, for instant CV updates: copy `docs/cv-repo-workflow.yml` into the CV repo as
   `.github/workflows/notify-site.yml`, and give that repo a secret `SITE_DISPATCH_TOKEN`
   (fine-grained token, **Contents: read and write** on this repo). Without it, the CV
   still refreshes on every site push and once a week.

## Layout

```
.github/workflows/deploy.yml   build + deploy, including the CV compile
docs/                          design directions and the CV-repo workflow to copy
public/                        static files: figures, CV PDF, favicon
src/data/                      YAML content
src/layouts, components, pages, styles
_archive/                      old site, full-resolution figures, paper PDFs (not committed)
```
