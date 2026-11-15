#!/usr/bin/env python3
"""Generates every static HTML page, data.js, sitemap, robots, _headers, README, CHANGELOG.

Env overrides (for testing): WP_DATA_DIR (where the *.json live), WP_OUT_DIR (where output goes).
"""
import json, html as H, os, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "_build"
DATA_DIR = Path(os.environ.get("WP_DATA_DIR") or BUILD)
OUT = Path(os.environ.get("WP_OUT_DIR") or ROOT)
CANON = "https://wellpumpchart.pages.dev"
SITE = "Well Pump Reference Library"
CHECKED, CHECKED_ISO = "Nov 15, 2026", "2026-11-15"
ASSET_V = "20261115a"
OG_ALT = "Well Pump Reference Library: a well casing with a submersible pump, pressure tank and gauge in teal line art"
CF = ("<!-- Cloudflare Web Analytics --><script type='module' src='https://static.cloudflareinsights.com/beacon.min.js' "
      "data-cf-beacon='{\"token\": \"77996a705a3343ec9fd576f961e5d874\"}'></script><!-- End Cloudflare Web Analytics -->")
PRICE_RULE = ("Price = lowest in-stock price for a new unit of that exact model seen on a public US retailer or manufacturer-store listing "
              "(seller named and linked), checked on the date shown. No affiliate links. If no live price was found, a $ band is shown as an editorial estimate.")
BANDS = "$ under $250 · $$ $250–$600 · $$$ $600–$1,200 · $$$$ $1,200–$2,500 · $$$$$ over $2,500"
SAFETY = ("This is a reference, not installation advice. Confirm your well's depth, water level, recovery rate, casing size, and your electrical "
          "supply (voltage, phase, wire size, breaker) with a licensed well or pump installer and electrician before buying or installing anything. "
          "Specs change — check the manufacturer's current page.")
FONTS = ("https://fonts.googleapis.com/css2?family=Archivo:wght@600;700;800&family=IBM+Plex+Mono:wght@400;500"
         "&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap")
FIELDS = ["id", "brand", "series", "model", "type", "well", "hp", "voltage", "phase", "flow_gpm", "flow_at_ft", "max_head_ft",
          "min_well_in", "tank_gal", "drawdown_gal", "drawdown_note", "max_psi", "setting", "warranty", "price_usd", "price_source",
          "price_url", "price_checked", "price_scale", "product_url", "curve_url", "spec_url", "notes"]

HERO_SVG = (BUILD / "hero.svg").read_text()
SECTIONS = json.loads((BUILD / "sections.json").read_text())

NAV = [("index.html", "Home")] + [(s["file"], s["nav"]) for s in SECTIONS] + [
    ("sizing.html", "Sizing"), ("compare.html", "Compare"), ("updates.html", "Updates"), ("index.html#about", "About")]


def e(s):
    return H.escape("" if s is None else str(s), quote=True)


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")


def write(name, text):
    p = OUT / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def js(obj):
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


# ---------------------------------------------------------------- data
def icon_for(brand):
    s = slug(brand)
    for ext in ("svg", "png"):
        if (ROOT / "icons" / f"{s}.{ext}").exists():
            return f"icons/{s}.{ext}"
    return None


def load_section(sec):
    path = DATA_DIR / sec["json"]
    raw = []
    if not path.exists():
        print(f"warn: {path.name} missing — rendering empty", file=sys.stderr)
    else:
        try:
            txt = path.read_text(encoding="utf-8").strip()
            raw = json.loads(txt) if txt else []
            if not isinstance(raw, list):
                raise ValueError("top level is not a list")
        except Exception as ex:  # partial writes by other processes etc.
            print(f"warn: {path.name} failed to parse ({ex}) — treating as empty", file=sys.stderr)
            raw = []
    items, used = [], set()
    for i, d in enumerate(raw):
        if not isinstance(d, dict):
            continue
        it = {k: d.get(k) for k in FIELDS}
        if not it["brand"] and not it["model"]:
            continue
        base = slug(it["id"]) if it["id"] else slug(f"{it['brand']}-{it['model']}") or f"item-{i}"
        iid, n = base, 2
        while iid in used or iid in ALL_IDS:
            iid, n = f"{base}-{n}", n + 1
        used.add(iid); ALL_IDS.add(iid)
        it["id"] = iid
        it["rid"] = "p-" + iid
        w = it["well"]
        it["well"] = [x for x in (w if isinstance(w, list) else [w] if w else []) if x in ("shallow", "deep")]
        if it["phase"] is not None:
            it["phase"] = str(it["phase"])
        it["_icon"] = icon_for(it["brand"] or "")
        items.append(it)
    return items


ALL_IDS = set()


# ---------------------------------------------------------------- shared chrome
def head(title, description, path, jsonld=None):
    url = CANON + (path if path != "/" else "/")
    typ = "website" if path == "/" else "article"
    ld = f'\n<script type="application/ld+json">{js(jsonld)}</script>' if jsonld else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{e(url)}">
<meta property="og:type" content="{typ}">
<meta property="og:site_name" content="{SITE}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{e(url)}">
<meta property="og:image" content="{CANON}/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{e(OG_ALT)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(description)}">
<meta name="twitter:image" content="{CANON}/og-image.png">
<link rel="icon" href="favicon.ico" sizes="any">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="theme.css?v={ASSET_V}">{ld}
</head>
"""


def nav(current):
    items = []
    for href, label in NAV:
        cur = ' aria-current="page"' if href == current else ""
        extra = ' <span class="cmp-n" hidden>0</span>' if href == "compare.html" else ""
        items.append(f'<li><a href="{href}"{cur}>{e(label)}{extra}</a></li>')
    return f"""<a class="skip" href="#main">Skip to content</a>
<nav class="topnav" aria-label="Primary">
  <div class="inner">
    <a class="brand" href="index.html">
      <svg width="28" height="28" viewBox="0 0 32 32" aria-hidden="true"><rect x="1" y="1" width="30" height="30" rx="6" fill="none" stroke="#3fc1c9" stroke-width="1.5"/><path d="M16 6 C16 6 8.5 14.5 8.5 19.5 a7.5 7.5 0 0 0 15 0 C23.5 14.5 16 6 16 6 Z" fill="none" stroke="#9be7ea" stroke-width="1.6"/><path d="M12.5 20 q3.5 -3 7 0" fill="none" stroke="#3fc1c9" stroke-width="1.5"/></svg>
      {SITE}
    </a>
    <button type="button" class="nav-toggle" aria-expanded="false" aria-controls="primary-nav" aria-label="Open menu">☰ Menu</button>
    <ul class="nav-links" id="primary-nav">{''.join(items)}</ul>
  </div>
</nav>
"""


def footer():
    return f"""<footer class="site-footer">
<p class="kofi">Free and ad-free. If this site helped you, <a href="https://ko-fi.com/marcustravis" target="_blank" rel="noopener">buy me a coffee →</a></p>
</footer>
<script>
(function () {{
  function syncNavH() {{
    var nav = document.querySelector(".topnav");
    if (!nav) return;
    document.documentElement.style.setProperty("--nav-h", Math.ceil(nav.getBoundingClientRect().height) + "px");
  }}
  syncNavH();
  window.addEventListener("resize", syncNavH);
  if (window.ResizeObserver && document.querySelector(".topnav")) {{
    new ResizeObserver(syncNavH).observe(document.querySelector(".topnav"));
  }}
}})();
</script>
"""


def hero(eyebrow, title, lede, compact=True, checked=True):
    chk = (f'<p class="checked">Data last checked: <time datetime="{CHECKED_ISO}">{CHECKED}</time> · '
           f'<a href="updates.html">What changed</a></p>') if checked else ""
    return f"""<header class="hero{' compact' if compact else ''}">
  <div class="hero-art">{HERO_SVG}</div>
  <div class="hero-copy">
    <span class="eyebrow">{e(eyebrow)}</span>
    <h1>{e(title)}</h1>
    <p class="lede">{lede}</p>
    {chk}
  </div>
</header>
"""


def safety():
    return f'<aside class="safety" role="note"><strong>Safety note.</strong> {e(SAFETY)}</aside>\n'


def page(name, title, desc, path, current, body, scripts="", jsonld=None, page_id=""):
    pid = f' data-page="{page_id}"' if page_id else ""
    html = head(title, desc, path, jsonld) + f"<body{pid}>\n" + f'<div class="page-bg"></div>\n' + nav(current)
    html += body + footer()
    html += f'<script src="compare.js?v={ASSET_V}"></script>\n<script src="nav.js?v={ASSET_V}"></script>\n{scripts}\n{CF}\n</body>\n</html>\n'
    write(name, html)


# ---------------------------------------------------------------- section pages
def write_section(sec, items):
    n = len(items)
    cols = sec["cols"]
    labels = {"brand": "Brand", "model": "Series / model", "type": "Type", "well": "Well", "hp": "HP", "vp": "Voltage / phase",
              "flow": "Flow gpm @ ft", "maxhead": "Max head / shutoff ft", "minwell": "Min well in", "tank": "Tank gal",
              "drawdown": "Drawdown gal", "maxpsi": "Max psi", "setting": "Setting / controls", "warranty": "Warranty",
              "price": "Price", "links": "Links"}
    sortable = {"links"}
    ths = ""
    for c in cols:
        num = ' class="num"' if c in ("hp", "flow", "maxhead", "minwell", "tank", "drawdown", "maxpsi") else ""
        inner = e(labels[c]) if c in sortable else f'<button type="button" class="th-btn" data-k="{c}">{e(labels[c])}</button>'
        if c == "drawdown":
            inner += '<span class="th-note">at the stated setting</span>'
        ths += f"<th{num} scope=\"col\">{inner}</th>"
    payload = [{k: v for k, v in it.items()} for it in items]
    ld = {"@context": "https://schema.org", "@type": "ItemList", "name": sec["title"] + " — " + SITE,
          "numberOfItems": n,
          "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": f"{it['brand'] or ''} {it['model'] or it['series'] or ''}".strip(),
                               "url": f"{CANON}/{sec['slug']}#{it['rid']}"} for i, it in enumerate(items)]}
    body = '<div class="wrap chart-wrap" id="main">\n'
    body += hero("Catalog · " + str(n) + " " + sec["card_noun"] if n else "Catalog", sec["title"], sec["lede"])
    body += safety()
    body += f"""  <div class="toolbar">
    <div class="fgroups" id="fgroups"></div>
    <div class="tools">
      <label class="search">Search
        <input type="search" id="search" placeholder="Brand, model, type" autocomplete="off">
      </label>
      <label class="sort">Sort
        <select id="sort"></select>
      </label>
    </div>
  </div>
  <p class="count" id="count" aria-live="polite"></p>
  <p class="table-caption" id="cap"><strong>Price rule:</strong> {e(PRICE_RULE)} <strong>Editorial estimate</strong> (no live price seen): {e(BANDS)}. Blank cells show “—” (not published / not found). Curve and data-sheet links go to the maker’s official page; curves are not reproduced here.</p>
  <div class="table-box">
    <table class="chart" aria-describedby="cap">
      <caption class="sr-only">{e(sec['title'])}: one row per model</caption>
      <thead><tr>{ths}</tr></thead>
      <tbody id="rows"></tbody>
    </table>
  </div>
  <div class="notes">
    <section><h2>How to read this chart</h2><ul>
      <li>Tick <strong>Compare</strong> on up to 4 rows (across any catalog), then open <a href="compare.html">Compare</a> to see them side by side.</li>
      <li>Click a column heading to sort; rows with no value for that column always sort last.</li>
      <li>Not sure what size you need? Start with <a href="sizing.html">sizing basics</a>.</li>
    </ul></section>
    <section><h2>Sources and limits</h2>
      <p>Facts come from official manufacturer pages and catalog PDFs, plus public retailer listings. Each row links its sources. Notes are written in our own words. Nothing is guessed: a missing number means it was not published or not found. Data last checked {CHECKED}.</p></section>
    <section><h2>Independence</h2>
      <p>No ads, no affiliate links, no tracking parameters. Every link goes straight to the manufacturer or retailer page it names.</p></section>
  </div>
</div>
"""
    scripts = (f'<script src="app.js?v={ASSET_V}"></script>\n<script src="scroll-hint.js?v={ASSET_V}"></script>\n'
               f'<script>\nconst DATA = {js(payload)};\n'
               f'initCatalog(DATA, {js({"noun": sec["noun"], "cols": cols, "filters": sec["filters"], "curveLabel": sec["curve_label"], "defaultSort": "brand"})});\n</script>')
    page(sec["file"], f"{sec['title']} · {SITE}", sec["description"], "/" + sec["slug"], sec["file"], body, scripts, ld)
    print(f"wrote {sec['file']}: {n} rows")


# ---------------------------------------------------------------- home
def write_home(sections_items):
    index = []
    for sec, items in sections_items:
        for it in items:
            name = (f"{it['series']} {it['model']}" if it["series"] and it["model"] and it["series"] not in it["model"] else (it["model"] or it["series"] or ""))
            tags = [t for t in [it["type"]] + [("Shallow well" if w == "shallow" else "Deep well") for w in it["well"]] if t]
            index.append({"name": name, "maker": it["brand"] or "", "tags": tags, "icon": it["_icon"], "section": sec["title"].split(":")[0],
                          "href": f"{sec['file']}#{it['rid']}"})
    cards = "".join(
        f'<a class="card" href="{s["file"]}"><span class="cnt">{len(items)} {s["card_noun"]}</span><span class="nm">{e(s["title"].split(":")[0])}</span>'
        f'<span class="ds">{e(s["card"])}</span><span class="go">Open catalog →</span></a>' for s, items in sections_items)
    cards += ('<a class="card" href="sizing.html"><span class="cnt">Explainer</span><span class="nm">Sizing basics</span>'
              '<span class="ds">How many gpm, how much head, which tank, and shallow vs deep wells — with worked examples.</span><span class="go">Read sizing basics →</span></a>')
    cards += ('<a class="card" href="compare.html"><span class="cnt">Tool</span><span class="nm">Compare</span>'
              '<span class="ds">Pick up to four rows from any catalog and see every field and source side by side.</span><span class="go">Open compare →</span></a>')
    total = len(index)
    body = '<div class="wrap chart-wrap" id="main">\n'
    body += hero("Independent well water reference", SITE,
                 "A free, ad-free, cross-brand reference for residential and light-agricultural well pumps and pressure systems: submersible and jet pumps, constant-pressure systems, pressure tanks, and controls.",
                 compact=False)
    body += safety()
    body += f"""  <section class="site-search" role="search" aria-labelledby="site-search-h">
    <h2 id="site-search-h">Search every product</h2>
    <label for="site-search">Pumps, tanks, and controls — by brand, model, or type</label>
    <input type="search" id="site-search" placeholder="Try Grundfos, 3-wire, 44 gal, pressure switch…" autocomplete="off" spellcheck="false" aria-describedby="site-status" aria-controls="site-results">
    <p class="sr-status" id="site-status" aria-live="polite">Searches all {total} products across every catalog.</p>
    <ul class="sr-list" id="site-results" hidden></ul>
  </section>
  <section class="grp">
    <h2>Start here</h2>
    <div class="grid">{cards}</div>
  </section>
  <div class="notes">
    <section>
      <h2>Why this exists</h2>
      <p>The U.S. Geological Survey estimates that around 43 million people in the United States get their household water from private domestic wells — wells owned and looked after by the household rather than a utility (<a href="https://www.usgs.gov/mission-areas/water-resources/science/domestic-private-supply-wells" target="_blank" rel="noopener">USGS overview</a>). Those households shop for pumps, tanks, and controls one brand site at a time. This library puts the specs side by side.</p>
    </section>
    <section>
      <h2>How to use it</h2>
      <p>Search above, or open a catalog. Each catalog is a dense, sortable chart with filter chips for brand, type, well depth, horsepower and phase. Tick <strong>Compare</strong> on up to four rows to line them up. New to sizing? Read <a href="sizing.html">sizing basics</a> first.</p>
    </section>
  </div>
  <section class="notes" id="about" style="display:block">
    <section>
      <h2>About this site</h2>
      <p>The Well Pump Reference Library is free and has no ads, no affiliate links, and no tracking parameters in its links. Facts come from official manufacturer pages and catalog PDFs and from public retailer listings, last checked {CHECKED}. Notes are written in original words; pump curves and marketing text are never copied, only linked to the maker’s official page.</p>
      <p><strong>Price rule.</strong> {e(PRICE_RULE)} If no live price was seen for that exact model, the cell shows an editorial band, labelled “Editorial estimate”: {e(BANDS)}.</p>
      <p><strong>Logos.</strong> Brand marks appear only once official ones are added (see <code>icons/README.md</code>); until then each brand is shown as a plain text badge. Specs change, so always check the manufacturer’s current page.</p>
      <p><a href="updates.html">See what changed →</a></p>
    </section>
  </section>
</div>
"""
    ld = {"@context": "https://schema.org", "@type": "WebSite", "name": SITE, "url": CANON + "/",
          "description": "Free, ad-free cross-brand reference for residential and light-ag well pumps and pressure systems."}
    scripts = f'<script>window.SEARCH_INDEX = {js(index)};</script>\n<script src="home-search.js?v={ASSET_V}"></script>'
    page("index.html", f"{SITE} — well pumps, tanks and controls compared",
         "Free, ad-free reference comparing residential and light-ag well pumps: submersible, jet, constant-pressure systems, pressure tanks and controls, with sizing basics and a compare tool.",
         "/", "index.html", body, scripts, ld)
    print("wrote index.html")


# ---------------------------------------------------------------- compare + data.js
def write_compare(sections_items):
    items = {}
    for sec, its in sections_items:
        for it in its:
            d = dict(it)
            d["section"] = sec["slug"]; d["sectionLabel"] = sec["title"].split(":")[0]; d["sectionFile"] = sec["file"]
            d["_curveLabel"] = sec["curve_label"]
            items[it["id"]] = d
    write("data.js", "/* Generated by _build/generate.py — all catalog items, used by compare.html. */\nwindow.WP_ITEMS = " + js(items) + ";\n")
    body = '<div class="wrap chart-wrap" id="main">\n'
    body += hero("Side by side", "Compare", "Up to four items from any catalog, every field and source in one view. Rows that are blank for all chosen items are hidden.", checked=False)
    body += safety()
    body += f"""  <div class="cmp-actions"><button type="button" class="btn" id="cmp-clear" hidden>Clear all</button>
    <span class="count">Selections are saved in this browser only. Prices: {e(PRICE_RULE)}</span></div>
  <div class="cmp-wrap" id="cmp-root" aria-live="polite"><div class="cmp-empty">Loading…</div></div>
</div>
"""
    page("compare.html", f"Compare · {SITE}", "Compare up to four well pumps, tanks, or controls side by side: every spec, price source and official link in one table.",
         "/compare", "compare.html", body, f'<script src="data.js?v={ASSET_V}"></script>', page_id="compare")
    # data.js must load before compare.js runs init; compare.js initialises on DOMContentLoaded, so order is fine.
    print("wrote compare.html, data.js")


# ---------------------------------------------------------------- sizing
SIZING = """
<div class="wrap" id="main">
""" + "{HERO}" + "{SAFETY}" + """
<article class="prose">
  <nav class="toc" aria-label="On this page"><strong>On this page</strong>
    <ol>
      <li><a href="#gpm">How many gpm do you need?</a></li>
      <li><a href="#tdh">Total dynamic head</a></li>
      <li><a href="#drawdown">Pressure tank drawdown</a></li>
      <li><a href="#shallow-deep">Shallow vs deep wells</a></li>
      <li><a href="#wires">2-wire vs 3-wire submersibles</a></li>
      <li><a href="#cp">Constant pressure vs conventional</a></li>
    </ol>
  </nav>

  <h2 id="gpm">1. How many gpm do you need?</h2>
  <p>Gallons per minute (gpm) is how fast the pump must deliver water when several things run at once. Two rough starting points installers use:</p>
  <ul>
    <li><strong>Fixture count:</strong> count the water outlets (sinks, toilets, showers and tubs, dishwasher, washer, hose bibs) and allow roughly <strong>1 gpm per fixture</strong>.</li>
    <li><strong>Bedroom rules:</strong> many charts land somewhere around 6–12 gpm for a typical 3-bedroom, 2-bath house. Treat any such chart as a ballpark, not a promise.</li>
  </ul>
  <div class="example"><p><strong>Example.</strong> A house with 2 toilets, 3 bathroom/kitchen sinks, 2 showers, a dishwasher, a washer and 2 hose bibs has 11 outlets. The one-gpm-per-fixture rule says about 11 gpm; in practice not everything runs at once, so many people would be comfortable with 8–10 gpm here. The pressure tank covers short peaks.</p></div>
  <p><strong>Irrigation adds on top.</strong> Add the flow of the sprinkler zone (or zones) that will run while the house is also using water. If one zone needs 8 gpm, the example house above is now planning for roughly 16–19 gpm.</p>
  <p><strong>Check the well, too.</strong> A pump that outruns the well’s recovery rate will pump it down and run dry. Your driller’s well report is the number that matters.</p>

  <h2 id="tdh">2. Total dynamic head (TDH)</h2>
  <p>Head is pressure expressed as feet of water. A pump’s curve shows how many gpm it delivers at a given total head, so you need your job’s total:</p>
  <p><span class="formula">TDH = vertical lift + pressure in feet + friction loss</span></p>
  <ul>
    <li><strong>Vertical lift:</strong> from the <em>pumping</em> water level (where the water sits while the pump runs, not the resting level) up to the pressure tank or house, including any height above the wellhead.</li>
    <li><strong>Pressure in feet:</strong> <span class="formula">psi × 2.31</span>. Use the pressure switch’s cut-out (the higher number), since the pump has to reach it.</li>
    <li><strong>Friction loss:</strong> look it up in a friction-loss table for your pipe material and size at your flow. Longer, thinner pipe loses more.</li>
  </ul>
  <div class="example">
    <p><strong>Worked example (made-up numbers).</strong> Pumping water level 120 ft, tank 5 ft above the wellhead: vertical lift = 125 ft.</p>
    <p>Switch set 40/60 psi: 60 × 2.31 = 138.6 ft, call it 139 ft.</p>
    <p>Suppose the friction table gives 4 ft per 100 ft for your pipe and flow, and you have 200 ft of pipe: 8 ft.</p>
    <p>TDH ≈ 125 + 139 + 8 = <strong>272 ft</strong>. You would look for a pump whose curve delivers your target gpm at about 272 ft, with some margin.</p>
  </div>

  <h2 id="drawdown">3. Pressure tank drawdown</h2>
  <p><strong>Drawdown</strong> is the water you actually get out of the tank between the pump turning on (cut-in) and off (cut-out). It is only a fraction of the tank’s total volume, and it shrinks as the pressure range rises. That is why two “44-gallon” tanks can differ, and why a stated drawdown is only meaningful at a stated pressure setting.</p>
  <p><strong>Why it matters:</strong> bigger drawdown means the pump runs longer and starts less often. Frequent short cycling wears the pump and the switch. Many manufacturers ask for roughly <strong>at least one minute of run time</strong> per cycle as general guidance, so the drawdown you want is about your pump’s gpm × 1 minute.</p>
  <div class="mini-box"><table class="mini">
    <thead><tr><th>Switch setting</th><th>Approx. drawdown as share of tank volume*</th></tr></thead>
    <tbody><tr><td>30/50 psi</td><td>about 30%</td></tr><tr><td>40/60 psi</td><td>about 26%</td></tr><tr><td>50/70 psi</td><td>about 23%</td></tr></tbody>
  </table></div>
  <p class="count">*Ideal-gas estimate with the correct precharge; real tanks differ. Use the manufacturer’s own drawdown table.</p>
  <div class="example"><p><strong>Example.</strong> A 10 gpm pump at 40/60 psi wants roughly 10 gallons of drawdown for a one-minute run. At about 26%, that points to a tank with around 40 gallons or more of total volume. Compare tanks by their listed drawdown at your setting, not by total gallons.</p></div>
  <p><strong>Precharge:</strong> the air pressure in the tank should be about <strong>2 psi below the cut-in</strong> pressure (38 psi for a 40/60 switch). Check it with the pump switched off at the breaker and the tank drained of water pressure, using a tire gauge on the air valve. Disconnect power first.</p>

  <h2 id="shallow-deep">4. Shallow vs deep wells</h2>
  <p>A pump above ground can only <em>pull</em> water up with suction, and atmospheric pressure limits how far. In practice about <strong>25 ft</strong> of lift is the working limit for a shallow-well pump (less at altitude, with long pipe runs, or with warm water).</p>
  <ul>
    <li><strong>Shallow-well jet pumps</strong> sit at the wellhead or in the house, with one pipe into the well.</li>
    <li><strong>Deep-well jets</strong> put an ejector down in the well so the pump can serve deeper water, using two pipes. They get less efficient the deeper they work.</li>
    <li><strong>Submersibles</strong> sit in the water and <em>push</em> it up, so depth is limited by pump head and motor, not suction. They are the usual choice for deeper wells.</li>
  </ul>

  <h2 id="wires">5. 2-wire vs 3-wire submersibles</h2>
  <ul>
    <li><strong>2-wire:</strong> the motor’s starting parts are inside the motor, so only two power wires (plus ground) run down the well and no control box is needed. Simple, but typically offered in smaller sizes.</li>
    <li><strong>3-wire:</strong> starting parts live in an above-ground <strong>control box</strong>, with three power wires (plus ground) down the well. The box can be serviced without pulling the pump, and 3-wire motors go to larger sizes.</li>
  </ul>
  <p>A 3-wire motor needs the matching control box for its horsepower, voltage and brand specification — see the <a href="controls.html">Controls</a> catalog. Three-phase motors use different starters and are not covered by this rule of thumb.</p>

  <h2 id="cp">6. Constant pressure vs conventional</h2>
  <ul>
    <li><strong>Conventional:</strong> a pressure switch and a tank. Pressure swings between cut-in and cut-out (often 20 psi apart). Simple and lower cost.</li>
    <li><strong>Constant pressure:</strong> a variable-speed drive adjusts the motor speed to hold one pressure, usually with a much smaller tank. Steadier showers, softer starts, and often smoother on the electrical supply, at higher cost and with a drive that has to match the motor.</li>
  </ul>
  <p>Browse both in the <a href="constant-pressure.html">Constant-pressure systems</a> and <a href="tanks.html">Pressure tanks</a> catalogs.</p>
</article>
</div>
"""


def write_sizing():
    body = SIZING.replace("{HERO}", hero("Explainer", "Sizing basics",
                                         "Plain-words guidance for picking flow, head, tank size, and pump type, with small worked examples. Rough guidance, not a design.", checked=False)).replace("{SAFETY}", safety())
    page("sizing.html", f"Sizing basics: gpm, head, tanks, shallow vs deep · {SITE}",
         "Original-words well pump sizing basics: how many gpm you need, total dynamic head with a worked example, pressure tank drawdown, shallow vs deep wells, 2-wire vs 3-wire, and constant pressure.",
         "/sizing", "sizing.html", body)
    print("wrote sizing.html")


# ---------------------------------------------------------------- updates / changelog
def changelog(stats):
    c = stats["counts"]
    lines = ", ".join(f"{s['title'].split(':')[0]} {c[s['slug']]}" for s in SECTIONS)
    return [{
        "month": "November 2026", "iso": CHECKED_ISO, "date": CHECKED,
        "title": "Launched v1",
        "items": [
            f"Launched version 1 with five catalogs: {lines} — {stats['total']} rows in all.",
            "Added sizing basics (gpm, total dynamic head, tank drawdown, shallow vs deep, 2-wire vs 3-wire, constant pressure vs conventional) with worked examples.",
            "Added the Compare tool: tick up to four rows from any catalog and view every field, source and link side by side.",
            f"Sourcing: specs come from official manufacturer pages and catalog PDFs, plus public retailer listings, checked {CHECKED}. Notes are in our own words; pump curves are linked, never reproduced.",
            f"Prices: {stats['priced']} rows have a live retailer price with a source link and check date; {stats['estimated']} show an editorial band. {PRICE_RULE}",
            f"Editorial price bands (shown only when no live price was seen): {BANDS}.",
        ]}]


def write_updates(stats):
    log = changelog(stats)
    entries = "".join(
        f'<div class="log"><h3>{e(x["month"])} — {e(x["title"])}</h3><p><time datetime="{x["iso"]}">{x["date"]}</time></p><ul>' +
        "".join(f"<li>{e(i)}</li>" for i in x["items"]) + "</ul></div>" for x in log)
    body = '<div class="wrap" id="main">\n' + hero("Changelog", "Updates", "A short, plain-English monthly record of what changed on this site.", checked=False)
    body += f'<article class="prose">{entries}</article>\n</div>\n'
    page("updates.html", f"Updates · {SITE}", "Monthly changelog for the Well Pump Reference Library: what was added, how data was sourced, and the price rule.",
         "/updates", "updates.html", body)
    md = "# Changelog\n\nAll notable changes to the Well Pump Reference Library, by month.\n\n"
    for x in log:
        md += f"## {x['month']} — {x['title']} ({x['date']})\n\n" + "".join(f"- {i}\n" for i in x["items"]) + "\n"
    write("CHANGELOG.md", md)
    print("wrote updates.html, CHANGELOG.md")


# ---------------------------------------------------------------- 404, meta, readme
def write_404():
    pages = [("/", "Home"), *[("/" + s["slug"], s["title"].split(":")[0]) for s in SECTIONS], ("/sizing", "Sizing basics"), ("/compare", "Compare")]
    grid = "".join(f'<a class="card" href="{CANON}{p}"><span class="nm">{e(n)}</span><span class="go">Open →</span></a>' for p, n in pages)
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Page not found · {SITE}</title>
<meta name="robots" content="noindex">
<link rel="icon" href="{CANON}/favicon.ico" sizes="any">
<link rel="icon" href="{CANON}/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{CANON}/apple-touch-icon.png">
<link rel="stylesheet" href="{FONTS.replace('&', '&amp;')}">
<link rel="stylesheet" href="{CANON}/theme.css">
<script>
(function(){{var p=location.pathname;if(p.length>1&&p.charAt(p.length-1)==="/")location.replace(p.slice(0,-1)+location.search+location.hash);}})();
</script>
</head>
<body>
<div class="page-bg"></div>
<div class="wrap" id="main">
  <span class="eyebrow">Error 404</span>
  <h1>Page not found</h1>
  <p class="lede">That page is not here. It may have moved, or the link has a typo. Try one of these instead.</p>
  <div class="grid">{grid}</div>
</div>
<footer class="site-footer">
<p class="kofi">Free and ad-free. If this site helped you, <a href="https://ko-fi.com/marcustravis" target="_blank" rel="noopener">buy me a coffee →</a></p>
</footer>
{CF}
</body>
</html>
"""
    write("404.html", html)
    print("wrote 404.html")


def write_meta():
    paths = ["/"] + ["/" + s["slug"] for s in SECTIONS] + ["/sizing", "/compare", "/updates"]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm += [f"  <url><loc>{CANON}{p}</loc><lastmod>{CHECKED_ISO}</lastmod></url>" for p in paths]
    sm.append("</urlset>")
    write("sitemap.xml", "\n".join(sm) + "\n")
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {CANON}/sitemap.xml\n")
    write("_headers",
          f"# {CANON.removeprefix('https://')} is the canonical address; other hostnames point search engines here.\n"
          f"/*\n  Link: <{CANON}/:splat>; rel=\"canonical\"\n"
          "  X-Content-Type-Options: nosniff\n"
          "  Referrer-Policy: strict-origin-when-cross-origin\n"
          "  X-Frame-Options: SAMEORIGIN\n")
    write("README.md", f"""# {SITE}

**Live site:** [{CANON}]({CANON})

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
""")
    write("icons/README.md", """# Brand icons

Drop a brand's **official** mark here as `<brand-slug>.svg` or `<brand-slug>.png` (for example `grundfos.svg`, `franklin-electric.png`; the slug is the brand name lower-cased with non-alphanumerics replaced by `-`). The generator picks it up automatically on the next run.

Rules:
- Only official brand marks from the manufacturer's own brand/press/media page. No recreated or traced logos.
- List the source URL for every file in the table below.
- Until an icon exists for a brand, the site shows a plain text badge with the brand name.

| File | Brand | Source URL |
| --- | --- | --- |
| _(none yet — text badges are used)_ | | |
""")
    print("wrote sitemap, robots, _headers, README, icons/README.md")


def main():
    sections_items = [(s, load_section(s)) for s in SECTIONS]
    counts = {s["slug"]: len(i) for s, i in sections_items}
    allitems = [it for _, i in sections_items for it in i]
    priced = sum(1 for it in allitems if it["price_usd"] is not None)
    stats = {"counts": counts, "total": len(allitems), "priced": priced, "estimated": len(allitems) - priced}
    for s, i in sections_items:
        write_section(s, i)
    write_home(sections_items)
    write_compare(sections_items)
    write_sizing()
    write_updates(stats)
    write_404()
    write_meta()
    print("DONE", stats)


if __name__ == "__main__":
    main()
