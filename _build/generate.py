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
CHECKED, CHECKED_ISO = "Nov 22, 2026", "2026-11-22"   # last monthly data check
LAUNCH, LAUNCH_ISO = "Nov 15, 2026", "2026-11-15"
ASSET_V = "20261120a"
BUILT, BUILT_ISO = "Nov 22, 2026", "2026-11-22"   # last site (not data) update; sitemap lastmod
INDEXNOW_KEY = "acfcbfb122853f68d9e9f8acec0d56ab"
CREATOR = {"@type": "Person", "name": "Marcus Travis"}
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
         "&family=IBM+Plex+Sans:wght@400;500;600;700&display=optional")
FIELDS = ["id", "brand", "series", "model", "type", "well", "hp", "voltage", "phase", "flow_gpm", "flow_at_ft", "max_head_ft",
          "min_well_in", "tank_gal", "drawdown_gal", "drawdown_note", "max_psi", "setting", "warranty", "price_usd", "price_source",
          "price_url", "price_checked", "price_scale", "product_url", "curve_url", "spec_url", "notes"]

HERO_SVG = (BUILD / "hero.svg").read_text()
SECTIONS = json.loads((BUILD / "sections.json").read_text())

NAV = [("index.html", "Home")] + [(s["file"], s["nav"]) for s in SECTIONS] + [
    ("sizing.html", "Sizing"), ("faq.html", "FAQ"), ("compare.html", "Compare"), ("updates.html", "Updates"), ("index.html#about", "About")]


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
    if isinstance(jsonld, list):
        jsonld = {"@context": "https://schema.org", "@graph": [{k: v for k, v in x.items() if k != "@context"} for x in jsonld]}
    ld = f'\n<script type="application/ld+json">{js(jsonld)}</script>' if jsonld else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
<meta name="google-site-verification" content="DBsd4dRo6CszvxQNH2xXlYTnwq2I4v30uIsV_nwwEc8">
<meta name="msvalidate.01" content="77C3B18F4D942281667A47021926052C">
<link rel="canonical" href="{e(url)}">
<meta property="og:type" content="{typ}">
<meta property="og:site_name" content="{SITE}">
<meta property="og:locale" content="en_US">
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
<link rel="stylesheet" href="{FONTS.replace('&', '&amp;')}">
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
    html += "<main>\n" + body + "</main>\n" + footer()
    html += f'<script src="compare.js?v={ASSET_V}"></script>\n<script src="nav.js?v={ASSET_V}"></script>\n{scripts}\n{CF}\n</body>\n</html>\n'
    write(name, html)



# ---------------------------------------------------------------- SEO helpers (Nov 2026 SEO pass)
SEO_TITLE = {
    "submersible": "Submersible Well Pump Comparison Chart ({n} models)",
    "jet": "Jet Pump Comparison Chart: Shallow and Deep Well ({n} models)",
    "constant-pressure": "Constant-Pressure Well Pump Systems Compared ({n} models)",
    "tanks": "Well Pressure Tank Comparison Chart: Size and Drawdown ({n} tanks)",
    "controls": "Well Pump Controls Compared: Switches, Control Boxes, VFDs ({n})",
}
HP_RANGES = [("≤1/2", lambda h: h <= 0.5), ("3/4–1", lambda h: 0.5 < h <= 1), ("1.5–2", lambda h: 1 < h < 3), ("3+", lambda h: h >= 3)]


def _has(v):
    return v is not None and v != ""


def money(v):
    return f"${v:,.0f}"


def pstats(items, skip_types=()):
    p = sorted(float(it["price_usd"]) for it in items if it["price_usd"] is not None and not any(t in (it["type"] or "") for t in skip_types))
    if not p:
        return None
    mid = len(p) // 2
    med = p[mid] if len(p) % 2 else (p[mid - 1] + p[mid]) / 2
    return {"n": len(p), "min": money(p[0]), "max": money(p[-1]), "med": money(med)}


def chips_html(sec, items):
    """Same chips app.js builds, rendered at build time so the toolbar has its final height before scripts run (no layout shift)."""
    out = []
    for gk in sec["filters"]:
        if gk in ("brand", "type"):
            vals = sorted({it[gk] for it in items if _has(it[gk])}, key=lambda x: x.lower())
            opts = [(v, v, sum(1 for it in items if it[gk] == v)) for v in vals]
            label = "Brand" if gk == "brand" else "Type"
        elif gk == "well":
            opts = [(v, l, sum(1 for it in items if v in it["well"])) for v, l in (("shallow", "Shallow well"), ("deep", "Deep well"))]
            label = "Well depth"
        elif gk == "hp":
            opts = [(str(i), r[0] + " HP", sum(1 for it in items if _has(it["hp"]) and r[1](float(it["hp"])))) for i, r in enumerate(HP_RANGES)]
            label = "Horsepower"
        elif gk == "phase":
            opts = [(v, f"{v}-phase", sum(1 for it in items if _has(it["phase"]) and v in str(it["phase"]))) for v in ("1", "3")]
            label = "Phase"
        else:
            continue
        opts = [o for o in opts if o[2] > 0]
        if len(opts) < 2:
            continue
        b = "".join(f'<button type="button" class="chip" data-g="{gk}" data-v="{e(v)}" aria-pressed="false">{e(l)}<small>{n}</small></button>' for v, l, n in opts)
        out.append(f'<div class="fgroup"><span class="flabel">{e(label)}</span><div class="chips" role="group" aria-label="{e(label)}">'
                   f'<button type="button" class="chip" data-g="{gk}" data-v="" aria-pressed="true">All</button>{b}</div></div>')
    return "".join(out)


def crumbs(*pairs):
    """pairs of (name, path); Home is added first."""
    allp = [("Home", "/")] + list(pairs)
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": CANON + p} for i, (n, p) in enumerate(allp)]}


def related(current):
    links = [(s["file"], s["title"].split(":")[0]) for s in SECTIONS] + [("sizing.html", "Sizing basics"), ("faq.html", "Well pump FAQ"), ("compare.html", "Compare tool")]
    return ('<nav class="related" aria-label="Related pages"><strong>Related:</strong> ' +
            " · ".join(f'<a href="{h}">{e(n)}</a>' for h, n in links if h != current) + "</nav>\n")


def section_answer(sec, items):
    n = len(items)
    brands = len({it["brand"] for it in items if it["brand"]})
    ps = pstats(items, ("pump end only",) if sec["slug"] == "submersible" else ())
    price = (f" The {ps['n']} rows with a live retailer price (checked {CHECKED}) ran from {ps['min']} to {ps['max']}, "
             f"with a median of {ps['med']}. That is equipment only, not installation.") if ps else ""
    s = sec["slug"]
    if s == "submersible":
        txt = (f"A submersible well pump sits under water inside the well casing and pushes water up, so it is not limited by suction the way an "
               f"above-ground pump is. That makes it the usual choice once the water is deeper than about 25 ft. This chart compares {n} residential "
               f"submersibles for 4-inch wells from {brands} brands, 1/2 to 2 HP, including 2-wire models (no control box) and 3-wire models (need a matching "
               f"control box above ground). Pick by flow at your total head, using the official curve each row links to." + price.replace("rows with a live", "complete pump-and-motor units with a live"))
    elif s == "jet":
        txt = (f"A jet pump sits above ground and draws water up by suction. A shallow-well jet works to about 25 ft of lift; a convertible jet can serve "
               f"a deeper well with an ejector placed down the well, at lower flow as depth grows. This chart compares {n} shallow-well and convertible "
               f"jet pumps from {brands} brands, all dual-voltage 115/230 V, with flow at the lift and pressure each maker states." + price)
    elif s == "constant-pressure":
        txt = (f"A constant-pressure system uses a variable-frequency drive (VFD) to speed the pump up or down and hold one set pressure, instead of letting "
               f"pressure swing between a switch’s cut-in and cut-out. It usually needs only a small pressure tank. This chart compares {n} systems, "
               f"drives and all-in-one boosters from {brands} brands. The drive must be matched to the motor it runs." + price)
    elif s == "tanks":
        txt = (f"A pressure tank stores water under air pressure so the pump does not start every time a tap opens. Size it by drawdown, the water "
               f"delivered between cut-in and cut-out, not by total gallons: aim for about one minute of pump run time per cycle, so a 10 gpm pump wants "
               f"roughly 10 gallons of drawdown (about a 40-gallon-plus tank at 40/60 psi). This chart compares {n} tanks from {brands} brands." + price)
    else:
        txt = (f"Controls start, stop and protect the pump. A pressure switch turns it on at the cut-in pressure and off at cut-out (30/50 and 40/60 psi "
               f"are common factory settings). A 3-wire submersible motor needs a control box matched to its brand, horsepower and voltage. Pump "
               f"protectors guard against dry running and bad voltage, and VFDs give constant pressure. This chart compares {n} controls from {brands} brands." + price)
    return f'<section class="answer" aria-label="In short"><p><strong>In short.</strong> {e(txt)} See the <a href="faq.html">FAQ</a> and <a href="sizing.html">sizing basics</a> for more.</p></section>\n'


def dataset_ld(sec, items, title):
    vm = {"brand": "Brand", "model": "Series / model", "type": "Type", "well": "Well depth (shallow / deep)", "hp": "Horsepower", "vp": "Voltage and phase",
          "flow": "Flow (gpm) at stated head (ft)", "maxhead": "Maximum / shutoff head (ft)", "minwell": "Minimum well diameter (in)", "tank": "Total tank volume (gal)",
          "drawdown": "Drawdown (gal) at stated pressure setting", "maxpsi": "Maximum working pressure (psi)", "setting": "Pressure setting / controls",
          "warranty": "Warranty", "price": "Price (USD) with source and check date", "links": "Official product, curve and data sheet links"}
    return {"@context": "https://schema.org", "@type": "Dataset", "name": title, "description":
            f"{sec['description']} {len(items)} rows. Specs from official manufacturer pages and catalog PDFs; prices from public US retailer listings with "
            f"seller, link and check date, or an editorial $ band where no live price was seen. Data last checked {CHECKED}.",
            "url": f"{CANON}/{sec['slug']}", "creator": CREATOR, "publisher": CREATOR, "dateModified": CHECKED_ISO, "isAccessibleForFree": True,
            "inLanguage": "en-US", "spatialCoverage": "United States",
            "keywords": [sec["title"].split(":")[0], "well pump", "comparison chart", "specifications", "prices"],
            "variableMeasured": [vm[c] for c in sec["cols"] if c in vm],
            "includedInDataCatalog": {"@type": "DataCatalog", "name": SITE, "url": CANON + "/"}}


# ---------------------------------------------------------------- FAQ
def faq_items(sections_items):
    by = {s["slug"]: i for s, i in sections_items}
    n = {k: len(v) for k, v in by.items()}
    sub = pstats(by.get("submersible", []), ("pump end only",)); jet = pstats(by.get("jet", [])); cp = pstats(by.get("constant-pressure", []))
    tk = pstats(by.get("tanks", [])); ct = pstats(by.get("controls", []))
    sub115 = [it for it in by.get("submersible", []) if it["voltage"] and "115" in str(it["voltage"])]
    sub115_hp = max((float(it["hp"]) for it in sub115 if _has(it["hp"])), default=None)

    def rng(x, what):
        return f"{what}: {x['min']} to {x['max']} (median {x['med']}, {x['n']} priced)" if x else ""
    costs = "; ".join(r for r in [rng(sub, "submersible pump-and-motor units"), rng(jet, "jet pumps"), rng(cp, "constant-pressure systems and drives"),
                                  rng(tk, "pressure tanks"), rng(ct, "controls")] if r)
    v115 = (f"In this library, the 115 V submersibles are all {U_hp(sub115_hp)} HP or smaller, while every jet pump listed is dual-voltage 115/230 V and is "
            f"switched by a wiring change described in its manual. ") if sub115_hp else ""
    return [
        ("What size well pump do I need?",
         "Size a pump from two numbers: the flow you need in gallons per minute (gpm), and the total dynamic head (TDH) in feet the pump must work against "
         "at that flow. A common starting point is about 1 gpm per water fixture in the house, plus any irrigation zone that runs at the same time; a typical "
         "3-bedroom, 2-bath home often lands around 6 to 12 gpm. TDH is the lift from the pumping water level, plus the switch’s cut-out pressure × 2.31, plus "
         "pipe friction loss. Then pick a pump whose official curve delivers your gpm at your TDH, and never more gpm than the well can recover. Horsepower "
         "follows from the curve, not the other way round. Worked examples are on <a href=\"sizing.html\">Sizing basics</a>; have a licensed installer confirm."),
        ("Should I get a submersible pump or a jet pump?",
         "Use a jet pump when the water is shallow (within about 25 ft of the pump), or a convertible jet with a down-well ejector for a moderately deep well. "
         "It sits above ground, so it is easy to reach and service. Use a submersible for deeper wells and higher flow: it sits under water in the casing and "
         "pushes water up, so suction limits do not apply, and it runs quietly out of sight. The trade-off is that servicing a submersible means pulling it out "
         f"of the well. This library lists <a href=\"submersible.html\">{n.get('submersible', 0)} submersibles</a> and "
         f"<a href=\"jet.html\">{n.get('jet', 0)} jet pumps</a>."),
        ("What is the difference between a shallow-well and a deep-well jet pump?",
         "A shallow-well jet has its ejector built into the pump body and lifts water by suction through a single pipe, which limits it to about 25 ft of lift. "
         "A deep-well (convertible) jet puts the ejector down in the well and uses two pipes: one sends driving water down, the other brings it back up with the "
         "well water. That reaches deeper water, but flow falls as depth rises. Convertible pumps can be set up either way, and the ejector or jet kit is often "
         "sold separately. For example, Wayne lists its CWS50 convertible jet for deep-well use to 90 ft with a separate jet assembly."),
        ("How deep can a jet pump pull water?",
         "About 25 ft for a shallow-well jet. Suction is limited by air pressure: at sea level, atmospheric pressure (about 14.7 psi) can hold up a column of "
         "water roughly 34 ft tall at best, and pipe friction, altitude and warmer water cut that down, so about 25 ft is the practical limit. The "
         "shallow-well jets listed here from Goulds, Red Lion, Flint & Walling and Wayne are rated for lift to 25 ft. Deeper than that, use a deep-well jet with a down-well ejector or a submersible."),
        ("What is a constant-pressure well pump system?",
         "A constant-pressure system uses a variable-frequency drive (VFD) to change the motor’s speed so pressure stays near one set point, instead of swinging "
         "between a switch’s cut-in and cut-out (for example 40 and 60 psi). You get steadier pressure when several taps run, soft motor starts, and a much "
         "smaller pressure tank (a small one is still needed). Downsides are a higher price and a drive that must be matched to the motor and installed per the "
         f"maker’s manual. Compare <a href=\"constant-pressure.html\">{n.get('constant-pressure', 0)} systems and drives</a>."),
        ("What size pressure tank do I need?",
         "Size the tank by drawdown, the usable water between cut-in and cut-out, not by its total gallons. Pump and tank makers generally ask for at least about "
         "one minute of pump run time per cycle, so you want drawdown of roughly your pump’s gpm × 1 minute. At a 40/60 psi setting, drawdown is about a quarter "
         "of total tank volume, so a 10 gpm pump points to a tank of about 40 gallons or more. Check the maker’s own drawdown table for your setting. "
         f"Compare <a href=\"tanks.html\">{n.get('tanks', 0)} tanks</a> by drawdown."),
        ("What should the pressure tank air precharge be?",
         "About 2 psi below the pump’s cut-in pressure: 28 psi for a 30/50 switch, 38 psi for a 40/60 switch. Check it with the pump’s power off and the water "
         "pressure drained to zero, using a tire gauge on the tank’s air valve."),
        ("Should I set my pressure switch to 30/50 or 40/60 psi?",
         "Both are common factory settings with a 20 psi spread: the pump starts at the lower number and stops at the higher one. 40/60 gives stronger pressure at "
         "the taps, but the pump must reach 10 psi more (about 23 ft more head), and the same tank gives slightly less drawdown. Before raising the setting, check "
         "on the pump’s official curve that it can reach the new cut-out at your well’s depth, and reset the tank precharge to 2 psi below the new cut-in. "
         "Adjust only with the power off, following the switch maker’s instructions. Browse switches in <a href=\"controls.html\">Controls</a>."),
        ("What is the difference between a 2-wire and a 3-wire submersible pump?",
         "A 2-wire submersible has its starting parts inside the motor, so it needs no control box: two power wires plus a ground run down the well. A 3-wire "
         "motor keeps its starting parts (capacitor and relay) in a control box above ground, with three power wires plus a ground. The control box can be "
         "serviced without pulling the pump, and 3-wire motors are offered in larger sizes. A 3-wire motor needs the control box matched to its brand, "
         "horsepower and voltage. Both are single-phase; three-phase motors use different starters."),
        ("Should my well pump be 115 V or 230 V?",
         "Match the pump to the supply at the well. For the same power, a 230 V motor draws about half the current of a 115 V motor, so it can use smaller wire "
         "over a long run down the well, which is why most submersibles are 230 V. " + v115 +
         "Have an electrician check wire size, voltage drop and the breaker."),
        ("How much does a well pump cost?",
         f"Equipment prices seen in this library on {CHECKED} (lowest in-stock new-unit price on a public US retailer page): {costs}. These are parts only; "
         "wire, pipe, fittings, permits and labor are extra, and an installer quotes those. Rows without a live price show an editorial $ band instead."),
        ("How many people in the US get water from a private well?",
         "The U.S. Geological Survey estimates that around 43 million people in the United States get household water from private domestic wells, which the "
         "household owns and maintains rather than a utility "
         "(<a href=\"https://www.usgs.gov/mission-areas/water-resources/science/domestic-private-supply-wells\" target=\"_blank\" rel=\"noopener\">USGS</a>)."),
        ("Where do the specs and prices on this site come from?",
         "Specs come from official manufacturer pages and catalog PDFs; each row links its sources, and pump curves are linked, never reproduced. Prices are the "
         "lowest in-stock price for a new unit of that exact model on a public US retailer or manufacturer-store listing, with the seller named and linked and the "
         f"check date shown. There are no ads and no affiliate links. Data was last checked {CHECKED}; see <a href=\"updates.html\">Updates</a>."),
        ("Can I install a well pump myself?",
         "This site is a reference, not installation advice. Well pump work involves line-voltage wiring, heavy equipment over an open well, and a risk of "
         "contaminating the water supply, and local rules may require a licensed contractor. Confirm your well’s depth, water level, recovery rate, casing size "
         "and electrical supply with a licensed well or pump installer and an electrician before buying or installing anything."),
    ]


def U_hp(h):
    return {0.5: "1/2", 0.75: "3/4", 0.333: "1/3"}.get(h, f"{h:g}")


def strip_tags(s):
    return H.unescape(re.sub(r"<[^>]+>", "", s))


def write_faq(sections_items):
    qa = faq_items(sections_items)
    toc = "".join(f'<li><a href="#q{i + 1}">{e(q)}</a></li>' for i, (q, _) in enumerate(qa))
    body = '<div class="wrap" id="main">\n' + hero("Questions and answers", "Well pump FAQ",
                                                   "Short, plain-English answers to the questions people ask most about well pumps, pressure tanks and controls, using this library’s data.", checked=True)
    body += safety()
    body += f'<article class="prose faq">\n  <nav class="toc" aria-label="On this page"><strong>On this page</strong><ol>{toc}</ol></nav>\n'
    body += "".join(f'  <h2 id="q{i + 1}">{e(q)}</h2>\n  <p>{a}</p>\n' for i, (q, a) in enumerate(qa))
    body += "</article>\n" + related("faq.html") + "</div>\n"
    ld = [{"@context": "https://schema.org", "@type": "FAQPage", "url": CANON + "/faq",
           "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": strip_tags(a)}} for q, a in qa]},
          crumbs(("Well pump FAQ", "/faq"))]
    page("faq.html", f"Well Pump FAQ: sizing, jet vs submersible, tanks, switches · {SITE}",
         "Plain answers on well pump sizing, submersible vs jet, shallow vs deep well jets, constant pressure, pressure tank size, 30/50 vs 40/60, 2-wire vs 3-wire, 115 V vs 230 V and cost.",
         "/faq", "faq.html", body, jsonld=ld)
    print("wrote faq.html")
    return qa


# ---------------------------------------------------------------- llms.txt
def write_llms(sections_items, qa):
    total = sum(len(i) for _, i in sections_items)
    head_ = (f"# {SITE}\n\n> Free, ad-free, cross-brand comparison charts of residential and light-agricultural well pumps and pressure systems: "
             f"submersible pumps, jet pumps, constant-pressure systems, pressure tanks and controls ({total} rows), plus a sizing guide, FAQ and a side-by-side compare tool.\n\n"
             f"Specs come from official manufacturer pages and catalog PDFs; every row links its sources, and pump curves are linked rather than reproduced. "
             f"Price rule: {PRICE_RULE} Editorial bands: {BANDS}. Data last checked {CHECKED} and refreshed monthly. No ads, no affiliate links. "
             f"Made by Marcus Travis. This is a reference, not installation advice; confirm sizing and wiring with a licensed well or pump installer and an electrician.\n\n")
    cat = "## Catalogs\n\n" + "".join(f"- [{s['title']}]({CANON}/{s['slug']}): {s['description']} ({len(i)} rows)\n" for s, i in sections_items)
    guides = (f"\n## Guides and tools\n\n- [Well pump FAQ]({CANON}/faq): sizing, submersible vs jet, shallow vs deep jets, constant pressure, tank size, precharge, 30/50 vs 40/60, 2-wire vs 3-wire, 115 V vs 230 V, cost\n"
              f"- [Sizing basics]({CANON}/sizing): gpm, total dynamic head with a worked example, tank drawdown, shallow vs deep wells\n"
              f"- [Compare]({CANON}/compare): up to four items side by side\n- [Updates]({CANON}/updates): monthly changelog\n"
              f"\n## Optional\n\n- [Full text for LLMs]({CANON}/llms-full.txt): every FAQ answer and every catalog row in plain text\n")
    write("llms.txt", head_ + cat + guides)
    full = head_ + "## FAQ\n\n" + "".join(f"### {q}\n\n{strip_tags(a)}\n\n" for q, a in qa)
    for s, items in sections_items:
        full += f"## {s['title']} ({len(items)} rows) — {CANON}/{s['slug']}\n\n"
        for it in items:
            bits = [f"{it['brand']} {it['model'] or it['series'] or ''}".strip()]
            if it["series"] and it["model"] and it["series"] not in it["model"]:
                bits.append(f"series {it['series']}")
            for k, lab in (("type", ""), ("hp", "HP "), ("voltage", ""), ("flow_gpm", "gpm "), ("max_head_ft", "max head ft "), ("min_well_in", "min well in "),
                           ("tank_gal", "tank gal "), ("drawdown_gal", "drawdown gal "), ("max_psi", "max psi "), ("setting", ""), ("warranty", "warranty ")):
                v = it[k]
                if _has(v):
                    if k == "flow_gpm" and _has(it["flow_at_ft"]):
                        bits.append(f"{v:g} gpm at {it['flow_at_ft']} ft" if isinstance(v, (int, float)) else f"{v} gpm at {it['flow_at_ft']} ft")
                    else:
                        bits.append(f"{lab}{v}")
            if it["well"]:
                bits.append("well: " + "/".join(it["well"]))
            if it["price_usd"] is not None:
                bits.append(f"price ${float(it['price_usd']):,.2f} at {it['price_source']} ({it['price_checked']})")
            elif it["price_scale"]:
                bits.append(f"editorial estimate {it['price_scale']}")
            if it["product_url"]:
                bits.append(f"official page {it['product_url']}")
            full += "- " + "; ".join(str(b) for b in bits) + "\n"
        full += "\n"
    write("llms-full.txt", full)
    write(f"{INDEXNOW_KEY}.txt", INDEXNOW_KEY)
    print("wrote llms.txt, llms-full.txt, IndexNow key")


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
    body += section_answer(sec, items)
    body += safety()
    body += f"""  <div class="toolbar">
    <div class="fgroups" id="fgroups">{chips_html(sec, items)}</div>
    <div class="tools">
      <label class="search">Search
        <input type="search" id="search" placeholder="Brand, model, type" autocomplete="off">
      </label>
      <label class="sort">Sort
        <select id="sort"></select>
      </label>
    </div>
  </div>
  <p class="count" id="count" aria-live="polite">{"Showing " + str(n) + " of " + str(n) + " " + e(sec["noun"]) if n else "0 " + e(sec["noun"]) + " — no rows yet"}</p>
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
""" + related(sec["file"]) + """</div>
"""
    scripts = (f'<script src="app.js?v={ASSET_V}"></script>\n<script src="scroll-hint.js?v={ASSET_V}"></script>\n'
               f'<script>\nconst DATA = {js(payload)};\n'
               f'initCatalog(DATA, {js({"noun": sec["noun"], "cols": cols, "filters": sec["filters"], "curveLabel": sec["curve_label"], "defaultSort": "brand"})});\n</script>')
    title = SEO_TITLE.get(sec["slug"], sec["title"]).format(n=n)
    ld = [dataset_ld(sec, items, title), crumbs((sec["title"].split(":")[0], "/" + sec["slug"])), ld]
    page(sec["file"], f"{title} · {SITE}", sec["description"], "/" + sec["slug"], sec["file"], body, scripts, ld)
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
    cards += ('<a class="card" href="faq.html"><span class="cnt">Answers</span><span class="nm">Well pump FAQ</span>'
              '<span class="ds">Submersible vs jet, shallow vs deep, tank size, 30/50 vs 40/60, 2-wire vs 3-wire, 115 V vs 230 V, and cost.</span><span class="go">Read the FAQ →</span></a>')
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
      <h2>Quick answers</h2>
      <p><strong>Submersible or jet?</strong> A jet pump sits above ground and lifts by suction, so a shallow-well jet works to about 25 ft; deeper wells usually take a submersible, which sits in the water and pushes it up. <strong>What size?</strong> Work out the gpm you need and the total head at that flow, then match a pump’s official curve. <strong>Which tank?</strong> Pick by drawdown, about one minute of pump run time per cycle. More in the <a href="faq.html">FAQ</a> and <a href="sizing.html">sizing basics</a>.</p>
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
      <p><strong>Logos.</strong> Official brand marks are shown where the maker’s own site offers one (sources in <code>icons/README.md</code>); other brands appear as a plain text badge. Marks belong to their owners. Specs change, so always check the manufacturer’s current page.</p>
      <p><a href="updates.html">See what changed →</a></p>
    </section>
  </section>
</div>
"""
    ld = {"@context": "https://schema.org", "@type": "WebSite", "name": SITE, "alternateName": "WellPumpChart", "url": CANON + "/",
          "description": "Free, ad-free cross-brand reference for residential and light-ag well pumps and pressure systems.",
          "inLanguage": "en-US", "creator": CREATOR, "publisher": CREATOR,
          "potentialAction": {"@type": "SearchAction", "target": {"@type": "EntryPoint", "urlTemplate": CANON + "/?q={search_term_string}"},
                              "query-input": "required name=search_term_string"}}
    scripts = f'<script>window.SEARCH_INDEX = {js(index)};</script>\n<script src="home-search.js?v={ASSET_V}"></script>'
    page("index.html", f"Well Pump Comparison Chart: pumps, tanks and controls · {SITE}",
         f"Free, ad-free charts comparing {total} residential well pumps, pressure tanks and controls across brands: submersible, jet and constant-pressure, with sourced prices, a sizing guide and FAQ.",
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
    page("compare.html", f"Compare well pumps side by side · {SITE}", "Compare up to four well pumps, tanks, or controls side by side: every spec, price source and official link in one table.",
         "/compare", "compare.html", body, f'<script src="data.js?v={ASSET_V}"></script>', page_id="compare", jsonld=crumbs(("Compare", "/compare")))
    # data.js must load before compare.js runs init; compare.js initialises on DOMContentLoaded, so order is fine.
    print("wrote compare.html, data.js")


# ---------------------------------------------------------------- sizing
SIZING = """
<div class="wrap" id="main">
""" + "{HERO}" + "{SAFETY}" + """
<article class="prose">
  <p><strong>In short.</strong> Size a well pump from the flow you need (gpm) and the total dynamic head (feet) at that flow, then pick a pump whose official curve meets both without out-pumping the well. Size the pressure tank by drawdown, about one minute of pump run time per cycle. Shallow water (about 25 ft or less) can use a jet pump; deeper wells usually need a submersible. Quick answers are in the <a href="faq.html">FAQ</a>.</p>
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
{RELATED}</div>
"""


def write_sizing():
    body = SIZING.replace("{HERO}", hero("Explainer", "Sizing basics",
                                         "Plain-words guidance for picking flow, head, tank size, and pump type, with small worked examples. Rough guidance, not a design.", checked=False)).replace("{SAFETY}", safety()).replace("{RELATED}", related("sizing.html"))
    ld = [{"@context": "https://schema.org", "@type": "Article", "headline": "How to size a well pump and pressure tank", "url": CANON + "/sizing",
           "author": CREATOR, "publisher": CREATOR, "dateModified": BUILT_ISO, "inLanguage": "en-US",
           "about": ["well pump sizing", "total dynamic head", "pressure tank drawdown", "jet pump", "submersible pump"]},
          crumbs(("Sizing basics", "/sizing"))]
    page("sizing.html", f"How to size a well pump and pressure tank: gpm, head, drawdown · {SITE}",
         "How to size a well pump: how many gpm you need, total dynamic head with a worked example, pressure tank drawdown, shallow vs deep wells, 2-wire vs 3-wire, and constant pressure.",
         "/sizing", "sizing.html", body, jsonld=ld)
    print("wrote sizing.html")


# ---------------------------------------------------------------- updates / changelog
# Monthly data refreshes, newest first.
MONTHLY = [{
    "month": "November 2026", "iso": "2026-11-22", "date": "Nov 22, 2026",
    "title": "Monthly data refresh",
    "items": [
        "Re-checked all 308 rows against official manufacturer pages, catalogs and data sheets plus public retailer listings on Nov 22, 2026; the library now has 312 rows.",
        "Prices: all 207 existing live prices were re-read on their retailer pages; one changed (Goulds J15S, $850.46 to $879.12). Ten rows that had only an editorial band now show a live price: Myers HJ50S, HJ75S, HJ100S, MPNC, MPND and MPNE; Wayne SWS50; Water Worker HT-20B; Franklin MonoDrive XT (NEMA 4); and Franklin Pumptec.",
        "Specs corrected or filled in from official sources: Goulds J5S flow and max pressure at 10 ft lift; Goulds J15 minimum casing size for deep-well use; Zoeller Air-E-Tainer drawdown now uses the 40/60 psi figures; Amtrol WX-103 size (7.6 gal), drawdown, max pressure and warranty; maximum pressure for Myers HJ jets and Sta-Rite HMS jets; warranty terms for Red Lion RL/RS submersibles, Flint & Walling CPJ/CPH jets and Franklin Pumptec units; input voltage for MonoDrive XT and SubDrive Utility UT3P; Square D 9013FYG2J33M4 setting; Pentek SPP enclosure types.",
        "Added 4 models: Flint & Walling CPJ03SB (1/3 HP shallow-well jet), Goulds CentriPro CB07412 and CB15412CR control boxes, and Pentek VIP Pro 5 HP control box.",
        "Marked discontinued per the manufacturer: Pentair Pro-Source PS steel pressure tanks (6 rows) and the Pentair FP217-1140 pressure switch.",
        "Links: 28 official links updated to their current addresses (mostly Franklin Electric pages that moved, plus Goulds, Pentair and Water Worker), and the Grundfos SQE curve PDF replaced with the current one. All official links were checked.",
        "Values that could not be confirmed this month were left unchanged.",
    ]}]


def changelog(stats):
    c = stats["counts"]
    lines = ", ".join(f"{s['title'].split(':')[0]} {c[s['slug']]}" for s in SECTIONS)
    return MONTHLY + [{
        "month": "November 2026", "iso": "2026-11-20", "date": "Nov 20, 2026",
        "title": "Search and AI-assistant pass",
        "items": [
            "Added a Well pump FAQ page (in the menu) with plain-English answers: pump size, submersible vs jet, shallow vs deep jets, jet pump depth, constant pressure, tank size and precharge, 30/50 vs 40/60, 2-wire vs 3-wire, 115 V vs 230 V, and cost ranges taken from this site’s own price data.",
            "Added a short “In short” answer at the top of each catalog and of sizing basics, plus Related links between catalogs, sizing, FAQ and Compare.",
            "Clearer page titles, structured data (WebSite with site search, Dataset for each catalog, FAQPage, BreadcrumbList), and an llms.txt / llms-full.txt summary for AI assistants.",
            "robots.txt now explicitly welcomes search and AI crawlers; the sitemap lists the FAQ and carries update dates; IndexNow is set up so Bing and others hear about changes quickly.",
            "Filter chips now render with the page, so catalog pages no longer jump while loading. No data changed in this pass.",
        ]}, {
        "month": "November 2026", "iso": LAUNCH_ISO, "date": LAUNCH,
        "title": "Launched v1",
        "items": [
            "Launched version 1 with five catalogs: Submersible pumps 101, Jet pumps 58, Constant-pressure systems 30, Pressure tanks 66, Controls 53 — 308 rows in all.",
            "Added sizing basics (gpm, total dynamic head, tank drawdown, shallow vs deep, 2-wire vs 3-wire, constant pressure vs conventional) with worked examples.",
            "Added the Compare tool: tick up to four rows from any catalog and view every field, source and link side by side.",
            "Sourcing: specs come from official manufacturer pages and catalog PDFs, plus public retailer listings, checked Nov 15, 2026. Notes are in our own words; pump curves are linked, never reproduced.",
            f"Prices: 207 rows have a live retailer price with a source link and check date; 101 show an editorial band. {PRICE_RULE}",
            f"Editorial price bands (shown only when no live price was seen): {BANDS}.",
        ]}]


def write_updates(stats):
    log = changelog(stats)
    entries = "".join(
        f'<div class="log"><h2>{e(x["month"])} — {e(x["title"])}</h2><p><time datetime="{x["iso"]}">{x["date"]}</time></p><ul>' +
        "".join(f"<li>{e(i)}</li>" for i in x["items"]) + "</ul></div>" for x in log)
    body = '<div class="wrap" id="main">\n' + hero("Changelog", "Updates", "A short, plain-English monthly record of what changed on this site.", checked=False)
    body += f'<article class="prose">{entries}</article>\n</div>\n'
    page("updates.html", f"Updates and changelog · {SITE}", "Monthly changelog for the Well Pump Reference Library: what was added, how data was sourced, and the price rule.",
         "/updates", "updates.html", body, jsonld=crumbs(("Updates", "/updates")))
    md = "# Changelog\n\nAll notable changes to the Well Pump Reference Library, by month.\n\n"
    for x in log:
        md += f"## {x['month']} — {x['title']} ({x['date']})\n\n" + "".join(f"- {i}\n" for i in x["items"]) + "\n"
    write("CHANGELOG.md", md)
    print("wrote updates.html, CHANGELOG.md")


# ---------------------------------------------------------------- 404, meta, readme
def write_404():
    pages = [("/", "Home"), *[("/" + s["slug"], s["title"].split(":")[0]) for s in SECTIONS], ("/sizing", "Sizing basics"), ("/faq", "FAQ"), ("/compare", "Compare")]
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
    paths = ["/"] + ["/" + s["slug"] for s in SECTIONS] + ["/sizing", "/faq", "/compare", "/updates"]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm += [f"  <url><loc>{CANON}{p}</loc><lastmod>{BUILT_ISO}</lastmod></url>" for p in paths]
    sm.append("</urlset>")
    write("sitemap.xml", "\n".join(sm) + "\n")
    bots = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "Claude-User", "PerplexityBot", "Perplexity-User",
            "Google-Extended", "Googlebot", "Bingbot", "Applebot", "Applebot-Extended", "DuckDuckBot"]
    write("robots.txt", "# Search engines and AI assistants are welcome to crawl, index and cite this free reference.\n\n" +
          "".join(f"User-agent: {b}\nAllow: /\n\n" for b in bots) + f"User-agent: *\nAllow: /\n\nSitemap: {CANON}/sitemap.xml\n")
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

Brand logos: see [`icons/README.md`](icons/README.md). Brands without an official icon appear as text badges.
""")
    if not (ROOT / "icons" / "README.md").exists():  # hand-maintained once icons exist
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
    qa = write_faq(sections_items)
    write_llms(sections_items, qa)
    write_updates(stats)
    write_404()
    write_meta()
    print("DONE", stats)


if __name__ == "__main__":
    main()
