/* Homepage search across every catalog.
   Index comes from window.SEARCH_INDEX, written into index.html by the generator.
   Matches brand, series/model, type, and tags; each result links to that row on its
   section page (section.html#p-id), which scrolls to and highlights the row. */
(function () {
  var INDEX = window.SEARCH_INDEX || [];
  var input = document.getElementById("site-search");
  var out = document.getElementById("site-results");
  var status = document.getElementById("site-status");
  if (!input || !out) return;
  var U = window.WPCompare ? window.WPCompare.util : null;
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; });
  }
  function norm(s) { return String(s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, ""); }
  INDEX.forEach(function (d) {
    d._name = norm(d.name); d._maker = norm(d.maker); d._tags = norm((d.tags || []).join(" | "));
  });

  function score(d, words) {
    var s = 0;
    for (var i = 0; i < words.length; i++) {
      var w = words[i], hit = 0;
      if (d._name.indexOf(w) === 0) hit = 6;
      else if (d._name.indexOf(" " + w) !== -1 || d._name.indexOf("-" + w) !== -1) hit = 5;
      else if (d._name.indexOf(w) !== -1) hit = 4;
      else if (d._maker.indexOf(w) !== -1) hit = 3;
      else if (d._tags.indexOf(w) !== -1) hit = 2;
      if (!hit) return 0; // every word must match somewhere
      s += hit;
    }
    return s;
  }

  function render() {
    var q = norm(input.value.trim());
    if (!q) {
      out.innerHTML = ""; out.hidden = true;
      status.textContent = INDEX.length ? "Searches all " + INDEX.length + " products across every catalog." : "No products have been added yet.";
      return;
    }
    var words = q.split(/\s+/).filter(Boolean);
    var hits = INDEX.map(function (d) { return { d: d, s: score(d, words) }; })
      .filter(function (h) { return h.s > 0; })
      .sort(function (a, b) { return b.s - a.s || a.d.name.localeCompare(b.d.name); });
    status.textContent = hits.length
      ? hits.length + (hits.length === 1 ? " product matches" : " products match") + " “" + input.value.trim() + "”"
      : "No products match “" + input.value.trim() + "”. Try a brand (Grundfos, Franklin, Goulds) or a type (tank, 3-wire, jet).";
    out.hidden = !hits.length;
    out.innerHTML = hits.slice(0, 60).map(function (h) {
      var d = h.d;
      var lead = U ? U.badge({ brand: d.maker, _icon: d.icon }, false) : esc(d.maker);
      var tags = (d.tags || []).slice(0, 4).map(function (t) { return '<span class="tag">' + esc(t) + "</span>"; }).join("");
      return '<li><a class="sr-item" href="' + esc(d.href) + '"><span class="sr-lead">' + lead + "</span>" +
        '<span class="sr-main"><span class="sr-name">' + esc(d.name) + '</span>' +
        '<span class="sr-maker">' + esc(d.maker) + '</span><span class="sr-tags">' + tags + "</span></span>" +
        '<span class="sr-sec">' + esc(d.section) + "</span></a></li>";
    }).join("");
  }

  input.addEventListener("input", render);
  input.addEventListener("keydown", function (ev) {
    if (ev.key === "Enter") {
      var first = out.querySelector("a");
      if (first) { ev.preventDefault(); location.href = first.getAttribute("href"); }
    } else if (ev.key === "ArrowDown") {
      var a = out.querySelector("a");
      if (a) { ev.preventDefault(); a.focus(); }
    }
  });
  out.addEventListener("keydown", function (ev) {
    if (ev.key !== "ArrowDown" && ev.key !== "ArrowUp") return;
    var links = [].slice.call(out.querySelectorAll("a"));
    var i = links.indexOf(document.activeElement);
    if (i === -1) return;
    ev.preventDefault();
    if (ev.key === "ArrowDown" && i < links.length - 1) links[i + 1].focus();
    else if (ev.key === "ArrowUp") (i > 0 ? links[i - 1] : input).focus();
  });
  var params = new URLSearchParams(location.search);
  if (params.get("q")) input.value = params.get("q");
  render();
})();
