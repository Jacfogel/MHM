# Understanding EI

A public, educational MkDocs site that explains Employment Insurance (EI) concepts in plain language using publicly available sources.

## Scope and safety

- Unofficial project
- Informational only
- Not legal advice
- Not case-specific guidance

## Tech stack

- [MkDocs](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- GitHub Pages deployment via GitHub Actions

## Local setup

1. Create and activate a Python virtual environment.
2. Install docs dependencies:
   ```bash
   pip install mkdocs mkdocs-material pymdown-extensions
   ```
3. Run local server:
   ```bash
   mkdocs serve
   ```
4. Open `http://127.0.0.1:8000`.

## Deployment (GitHub Pages)

1. Push the repository to GitHub.
2. In repository settings, enable **GitHub Pages** with source set to **GitHub Actions**.
3. The included workflow `.github/workflows/deploy-gh-pages.yml` will build and deploy on pushes to `main`.

## Where to edit content

- Site configuration: `mkdocs.yml`
- Main pages: `docs/`
- Topic pages: `docs/topics/`
- Process pages: `docs/process/`
- References: `docs/references/`
- Future visuals: `docs/assets/`
- Content planning notes: `docs/_notes/content-roadmap.md`

## Renaming later

To change the project title from "Understanding EI", update:

- `site_name` in `mkdocs.yml`
- Heading text in `docs/index.md`
- This README title
