# MHM Website

Static one-page marketing site for MHM.

## Cloudflare Workers deployment

Build command: leave blank (static HTML/CSS/JS)
Deploy command: `npx wrangler deploy`

The included `wrangler.jsonc` tells Cloudflare to serve this directory as static assets.

## Files
- `index.html` — page content
- `styles.css` — layout and visual design
- `script.js` — small client-side enhancements
- `wrangler.jsonc` — Cloudflare Workers configuration

## Before launch
Replace `hello@example.com` in `index.html` with the desired contact address.
