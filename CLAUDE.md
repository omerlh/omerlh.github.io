# Personal website

Static site for Omer Levi Hevroni, hosted on GitHub Pages. No frameworks, no JavaScript, no external requests.

## Layout
- `posts/YYYY-MM-DD-slug.md`: new posts. First line `# Title`, second `*Subtitle: ...*`. Plain Markdown (headings, lists, quotes, links, bold, italics).
- `build.py`: `python3 build.py` turns posts into `posts/<slug>/index.html` and refreshes "Latest" on `index.html`.
- `archive/`: old posts (2018-2022) from the previous WordPress blog. Static HTML, do not regenerate.
- `index.html`, `style.css`: home page and styles.

## Rules
- NEVER reference `omerlh.info`. The old domain lapsed in 2025 and belongs to someone else (redirects to a gambling site). Do not link to it, hotlink from it, or add it as a custom domain.
- Keep it dependency-free and self-contained (no CDN scripts, fonts, trackers).
- Posts must not contain infrastructure details (hostnames, ports, tool configs, credentials) or personal financial figures.
- Cross-post to Medium via "Import a story" so the canonical link points here.
