# Well Pump Reference Library

**Live site:** [https://wellpumpchart.pages.dev](https://wellpumpchart.pages.dev)

A free, ad-free, cross-brand reference for residential and light-agricultural well pumps and pressure systems: submersible pumps, jet pumps, constant-pressure systems, pressure tanks, and controls, plus sizing basics and a compare tool. Plain static HTML, CSS and JavaScript. Cloudflare Pages project name: `wellpumpchart`; **no build command** (the HTML is already generated), output directory = repo root.

There are no ads and no affiliate links. Links go to the manufacturer or retailer page they name.

## Local preview

From this folder: `python3 -m http.server`, then open `http://localhost:8000`.

## Regenerate pages

After editing the JSON in `_build/`:

```
python3 _build/generate.py
```

The site URL is set once as `CANON` in `_build/generate.py` (canonicals, sitemap, Open Graph). `ASSET_V` there cache-busts the CSS/JS. Missing, empty, or unparseable JSON files render as “No rows yet”.

## Data rules

Rows live in `_build/submersible.json`, `jet.json`, `constant-pressure.json`, `tanks.json`, and `controls.json`. The schema, the single price rule, and the hard rules (facts only from official pages and public listings, no invented numbers, no copied marketing text or curves) are in [`_build/SCHEMA.md`](_build/SCHEMA.md). After changing facts, update the monthly entry in `changelog()` in `generate.py` (this regenerates `CHANGELOG.md` and `updates.html`).

Brand logos: see [`icons/README.md`](icons/README.md). Until official marks are added, brands appear as text badges.
