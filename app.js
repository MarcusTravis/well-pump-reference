/* Shared catalog: filter chips, search, sortable columns, and chart rows.
   Needs compare.js (loaded first) for cell helpers and the Compare checkboxes. */
(function () {
  var U = window.WPCompare.util, esc = U.esc, has = U.has, NA = U.NA;
  var BAND_MID = { "$": 125, "$$": 425, "$$$": 900, "$$$$": 1850, "$$$$$": 3500 };

  function num(v) { return has(v) ? Number(v) : null; }
  function naIf(html) { return html ? html : NA; }
  function numCell(v) { return has(v) ? esc(U.fmtNum(v)) : NA; }

  // Column registry. s = sort value fn (numbers or strings; empty sorts last).
  var COLS = {
    brand: { label: "Brand", cls: "brandc", s: function (d) { return d.brand; },
      cell: function (d) {
        return U.badge(d, true) + '<label class="cmp"><input type="checkbox" class="cmp-cb" data-id="' + esc(d.id) + '"> Compare</label>';
      } },
    model: { label: "Series / model", cls: "modelc", s: function (d) { return (d.model || "") || (d.series || ""); },
      cell: function (d) {
        var main = d.model || d.series, sub = d.model && d.series && d.series !== d.model ? d.series : "";
        if (!main) return NA;
        return '<span class="cart">' + esc(main) + "</span>" + (sub ? '<span class="ser">' + esc(sub) + "</span>" : "") +
          (d.notes ? '<span class="sub">' + esc(d.notes) + "</span>" : "");
      } },
    type: { label: "Type", cls: "typec", s: function (d) { return d.type; }, cell: function (d) { return has(d.type) ? esc(d.type) : NA; } },
    well: { label: "Well", cls: "nw", s: function (d) { return U.wellTxt(d); }, cell: function (d) { return naIf(esc(U.wellTxt(d))); } },
    hp: { label: "HP", cls: "num", num: 1, s: function (d) { return num(d.hp); }, cell: function (d) { return naIf(esc(U.hpTxt(d.hp))); } },
    vp: { label: "Voltage / phase", cls: "nw", s: function (d) { return d.voltage; },
      cell: function (d) {
        var p = has(d.phase) ? esc(d.phase) + "-phase" : "";
        if (!has(d.voltage) && !p) return NA;
        return (has(d.voltage) ? esc(d.voltage) : NA) + (p ? '<span class="sub">' + p + "</span>" : "");
      } },
    flow: { label: "Flow gpm @ ft", cls: "num", num: 1, s: function (d) { return num(d.flow_gpm); }, cell: function (d) { return naIf(esc(U.flowTxt(d))); } },
    maxhead: { label: "Max head / shutoff ft", cls: "num", num: 1, s: function (d) { return num(d.max_head_ft); }, cell: function (d) { return numCell(d.max_head_ft); } },
    minwell: { label: "Min well in", cls: "num", num: 1, s: function (d) { return num(d.min_well_in); }, cell: function (d) { return numCell(d.min_well_in); } },
    tank: { label: "Tank gal", cls: "num", num: 1, s: function (d) { return num(d.tank_gal); }, cell: function (d) { return numCell(d.tank_gal); } },
    drawdown: { label: "Drawdown gal", cls: "num", num: 1, s: function (d) { return num(d.drawdown_gal); },
      cell: function (d) {
        if (!has(d.drawdown_gal)) return NA;
        return esc(U.fmtNum(d.drawdown_gal)) + (d.drawdown_note ? '<span class="sub">' + esc(d.drawdown_note) + "</span>" : "");
      } },
    maxpsi: { label: "Max psi", cls: "num", num: 1, s: function (d) { return num(d.max_psi); }, cell: function (d) { return numCell(d.max_psi); } },
    setting: { label: "Setting / controls", cls: "setc", s: function (d) { return d.setting; }, cell: function (d) { return has(d.setting) ? esc(d.setting) : NA; } },
    warranty: { label: "Warranty", cls: "warc", s: function (d) { return d.warranty; }, cell: function (d) { return has(d.warranty) ? esc(d.warranty) : NA; } },
    price: { label: "Price", cls: "nw", num: 1, price: 1,
      s: function (d) { return has(d.price_usd) ? Number(d.price_usd) : (BAND_MID[d.price_scale] || null); },
      cell: function (d) { return U.priceHtml(d); } },
    links: { label: "Links", cls: "", cell: function (d, o) { return U.linksHtml(d, o.curveLabel); } }
  };

  var HP_RANGES = [
    ["≤1/2", function (h) { return h <= 0.5; }],
    ["3/4–1", function (h) { return h > 0.5 && h <= 1; }],
    ["1.5–2", function (h) { return h > 1 && h < 3; }],
    ["3+", function (h) { return h >= 3; }]
  ];
  // Filter groups. opts(DATA) -> [{v,label}], test(d,v).
  var GROUPS = {
    brand: { label: "Brand", values: function (D) { return distinct(D, function (d) { return d.brand; }); }, test: function (d, v) { return d.brand === v; } },
    type: { label: "Type", values: function (D) { return distinct(D, function (d) { return d.type; }); }, test: function (d, v) { return d.type === v; } },
    well: { label: "Well depth", values: function () { return [{ v: "shallow", label: "Shallow well" }, { v: "deep", label: "Deep well" }]; }, test: function (d, v) { return (d.well || []).indexOf(v) !== -1; } },
    hp: { label: "Horsepower", values: function () { return HP_RANGES.map(function (r, i) { return { v: String(i), label: r[0] + " HP" }; }); }, test: function (d, v) { return has(d.hp) && HP_RANGES[Number(v)][1](Number(d.hp)); } },
    phase: { label: "Phase", values: function () { return [{ v: "1", label: "1-phase" }, { v: "3", label: "3-phase" }]; }, test: function (d, v) { return has(d.phase) && String(d.phase).indexOf(v) !== -1; } }
  };
  function distinct(D, f) {
    var seen = {}, out = [];
    D.forEach(function (d) { var v = f(d); if (has(v) && !seen[v]) { seen[v] = 1; out.push({ v: v, label: v }); } });
    return out.sort(function (a, b) { return a.label.localeCompare(b.label, undefined, { numeric: true }); });
  }
  function norm(s) { return String(s == null ? "" : s).toLowerCase(); }

  window.initCatalog = function (DATA, opts) {
    var cols = opts.cols, noun = opts.noun || "items", state = { sort: opts.defaultSort || "brand", dir: "asc", f: {}, q: "" };
    var rowsEl = document.getElementById("rows"), countEl = document.getElementById("count");
    if (!rowsEl) return;
    DATA.forEach(function (d) { d._curveLabel = opts.curveLabel; });

    // ---- filter chips ----
    var fwrap = document.getElementById("fgroups"), shown = [];
    fwrap.innerHTML = ""; // the generator pre-renders the same chips (no layout shift); rebuild them live here
    (opts.filters || []).forEach(function (gk) {
      var g = GROUPS[gk];
      if (!g) return;
      var vals = g.values(DATA).map(function (o) {
        return { v: o.v, label: o.label, n: DATA.filter(function (d) { return g.test(d, o.v); }).length };
      }).filter(function (o) { return o.n > 0; });
      if (vals.length < 2) return;
      shown.push(gk);
      var div = document.createElement("div");
      div.className = "fgroup";
      div.innerHTML = '<span class="flabel">' + esc(g.label) + '</span><div class="chips" role="group" aria-label="' + esc(g.label) + '">' +
        '<button type="button" class="chip" data-g="' + gk + '" data-v="" aria-pressed="true">All</button>' +
        vals.map(function (o) { return '<button type="button" class="chip" data-g="' + gk + '" data-v="' + esc(o.v) + '" aria-pressed="false">' + esc(o.label) + "<small>" + o.n + "</small></button>"; }).join("") +
        "</div>";
      fwrap.appendChild(div);
    });
    fwrap.addEventListener("click", function (ev) {
      var b = ev.target.closest(".chip");
      if (!b) return;
      var g = b.getAttribute("data-g"), v = b.getAttribute("data-v");
      if (v) state.f[g] = v; else delete state.f[g];
      b.parentNode.querySelectorAll(".chip").forEach(function (c) { c.setAttribute("aria-pressed", c === b ? "true" : "false"); });
      render();
    });
    function resetFilters() {
      state.f = {}; state.q = "";
      document.querySelectorAll(".chip").forEach(function (c) { c.setAttribute("aria-pressed", c.getAttribute("data-v") === "" ? "true" : "false"); });
      var s = document.getElementById("search"); if (s) s.value = "";
    }

    // ---- sort control ----
    var sel = document.getElementById("sort");
    if (sel) {
      var o = [];
      cols.forEach(function (k) {
        var c = COLS[k];
        if (!c || !c.s) return;
        var lab = c.price ? ["Price: cheapest first", "Price: priciest first"] : c.num ? [c.label + ": low → high", c.label + ": high → low"] : [c.label + ": A → Z", c.label + ": Z → A"];
        o.push('<option value="' + k + ':asc">' + esc(lab[0]) + '</option><option value="' + k + ':desc">' + esc(lab[1]) + "</option>");
      });
      sel.innerHTML = o.join("");
      sel.addEventListener("change", function () { var p = sel.value.split(":"); state.sort = p[0]; state.dir = p[1]; render(); });
    }
    document.querySelectorAll(".th-btn").forEach(function (b) {
      b.addEventListener("click", function () {
        var k = b.getAttribute("data-k");
        if (state.sort === k) state.dir = state.dir === "asc" ? "desc" : "asc";
        else { state.sort = k; state.dir = "asc"; }
        render();
      });
    });
    var search = document.getElementById("search");
    if (search) search.addEventListener("input", function () { state.q = norm(search.value.trim()); render(); });

    function matches(d) {
      for (var g in state.f) if (!GROUPS[g].test(d, state.f[g])) return false;
      if (!state.q) return true;
      var blob = norm([d.brand, d.series, d.model, d.type, d.notes, d.setting, d.voltage, d.warranty, U.wellTxt(d) || ""].join(" "));
      return state.q.split(/\s+/).every(function (w) { return blob.indexOf(w) !== -1; });
    }
    function sorted(rows) {
      var c = COLS[state.sort], dir = state.dir === "desc" ? -1 : 1;
      if (!c || !c.s) return rows;
      return rows.slice().sort(function (a, b) {
        var x = c.s(a), y = c.s(b), bx = !has(x), by = !has(y);
        if (bx || by) return bx && by ? 0 : bx ? 1 : -1; // blanks always last
        var r = c.num ? x - y : String(x).localeCompare(String(y), undefined, { numeric: true, sensitivity: "base" });
        return r * dir || String(a.brand).localeCompare(String(b.brand)) || String(a.model).localeCompare(String(b.model), undefined, { numeric: true });
      });
    }
    function syncControls() {
      if (sel) { var v = state.sort + ":" + state.dir; if ([].some.call(sel.options, function (x) { return x.value === v; })) sel.value = v; }
      document.querySelectorAll(".th-btn").forEach(function (b) {
        if (b.getAttribute("data-k") === state.sort) b.setAttribute("data-dir", state.dir); else b.removeAttribute("data-dir");
      });
    }
    function row(d) {
      return '<tr id="' + esc(d.rid) + '">' + cols.map(function (k) {
        var c = COLS[k];
        return '<td class="' + c.cls + '">' + c.cell(d, opts) + "</td>";
      }).join("") + "</tr>";
    }
    function render() {
      var rows = sorted(DATA.filter(matches));
      rowsEl.innerHTML = rows.map(row).join("") ||
        '<tr><td colspan="' + cols.length + '" class="empty">' + (DATA.length ? "Nothing matches those filters. Clear the search or choose All." : "No rows yet.") + "</td></tr>";
      if (countEl) countEl.textContent = DATA.length ? "Showing " + rows.length + " of " + DATA.length + " " + noun : "0 " + noun + " — no rows yet";
      syncControls();
      window.WPCompare.sync();
    }

    // Deep links: section.html#p-id scrolls to that row and flashes it.
    function focusHash(smooth) {
      var id = decodeURIComponent((location.hash || "").slice(1));
      if (!id || !/^p-/.test(id) || !DATA.some(function (d) { return d.rid === id; })) return;
      var tr = document.getElementById(id);
      if (!tr) { resetFilters(); render(); tr = document.getElementById(id); }
      if (!tr) return;
      var box = tr.closest(".table-box");
      if (box) {
        // The chart scrolls inside its own box, so scroll the box, then bring the box into view.
        box.scrollLeft = 0;
        box.scrollTop = Math.max(0, tr.offsetTop - 44);
        var nav = document.querySelector(".topnav"), navH = nav ? nav.getBoundingClientRect().height : 0;
        window.scrollTo({ top: Math.max(0, box.getBoundingClientRect().top + window.pageYOffset - navH - 70), behavior: smooth ? "smooth" : "instant" });
      }
      document.querySelectorAll("tr.row-flash").forEach(function (r) { r.classList.remove("row-flash"); });
      void tr.offsetWidth;
      tr.classList.add("row-flash");
      setTimeout(function () { tr.classList.remove("row-flash"); }, 3200);
    }
    render();
    if (location.hash) focusHash(false);
    window.addEventListener("hashchange", function () { focusHash(true); });
  };
})();
