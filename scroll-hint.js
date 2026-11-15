/* Horizontal-scroll cues for wide chart tables (same approach as ammochart.net).
   For every .table-box that is wider than the screen it adds:
   - a hint bar above the table with ◀ ▶ buttons and a "columns x–y of n" readout
   - fade shadows on whichever edge has more columns hidden
   - a scrollbar that sticks to the bottom of the window while the chart is on screen.
     It is drawn with plain elements (track + thumb), not the browser's native
     scrollbar, so it stays visible on phones and on systems with overlay scrollbars.
   Everything hides itself automatically when the whole table already fits.
*/
(function () {
  var touch = window.matchMedia && window.matchMedia("(hover: none)").matches;

  var css = `
.sh-hint{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:0 0 8px;padding:8px 10px 8px 12px;
  border:1px solid var(--line);border-radius:10px;background:var(--surface);color:var(--fg);font:600 13px var(--body,system-ui)}
.sh-hint[hidden]{display:none!important}
.sh-msg{display:inline-flex;align-items:center;gap:6px;flex:1 1 auto;min-width:0}
.sh-arrow{display:inline-block;color:var(--accent);animation:sh-nudge 1.4s ease-in-out infinite}
@keyframes sh-nudge{0%,100%{transform:translateX(0)}50%{transform:translateX(5px)}}
.sh-pos{color:var(--muted);font-weight:500;white-space:nowrap}
.sh-btns{display:inline-flex;gap:6px}
.sh-btn{font:700 14px var(--body,system-ui);line-height:1;width:36px;height:32px;border-radius:8px;cursor:pointer;
  border:1px solid var(--line);background:var(--btn,var(--surface));color:var(--fg)}
.sh-btn:hover:not(:disabled){border-color:var(--accent);color:var(--accent)}
.sh-btn:disabled{opacity:.35;cursor:default}
.sh-btn:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.sh-frame{position:relative}
.sh-edge{position:absolute;top:1px;bottom:1px;width:56px;pointer-events:none;opacity:0;transition:opacity .2s;z-index:4}
.sh-edge.l{left:1px;border-radius:12px 0 0 12px;background:linear-gradient(to right,var(--bg-2,var(--bg)),transparent)}
.sh-edge.r{right:1px;border-radius:0 12px 12px 0;background:linear-gradient(to left,var(--bg-2,var(--bg)),transparent)}
.sh-frame.can-l .sh-edge.l,.sh-frame.can-r .sh-edge.r{opacity:1}
.sh-on .table-box{scrollbar-width:none}
.sh-on .table-box::-webkit-scrollbar{display:none}
.sh-rail{position:sticky;bottom:0;z-index:6;margin-top:6px;padding:7px 8px calc(7px + env(safe-area-inset-bottom,0px));
  background:rgba(5,8,12,.94);border:1px solid var(--line);border-radius:10px;
  box-shadow:0 -6px 18px rgba(0,0,0,.45);backdrop-filter:blur(8px)}
.sh-rail[hidden]{display:none!important}
.sh-track{position:relative;height:14px;border-radius:7px;background:var(--bar-bg,rgba(61,232,255,.12));
  cursor:pointer;touch-action:none}
.sh-thumb{position:absolute;top:0;left:0;height:100%;min-width:40px;border-radius:7px;background:var(--accent);
  box-shadow:0 0 10px var(--cyan-glow,rgba(61,232,255,.45));cursor:grab;touch-action:none}
.sh-thumb:hover,.sh-rail.drag .sh-thumb{background:var(--cyan-2,var(--accent))}
.sh-rail.drag .sh-thumb{cursor:grabbing}
@media (max-width:640px){.sh-track{height:18px;border-radius:9px}.sh-thumb{border-radius:9px}.sh-pos{display:none}}
@media (prefers-reduced-motion:reduce){.sh-arrow{animation:none}}
`;
  var style = document.createElement("style");
  style.textContent = css;
  document.head.appendChild(style);

  document.querySelectorAll(".table-box").forEach(function (box) {
    var table = box.querySelector("table");
    if (!table) return;

    var shell = document.createElement("div");
    shell.className = "sh-shell";
    box.parentNode.insertBefore(shell, box);

    var hint = document.createElement("div");
    hint.className = "sh-hint";
    hint.setAttribute("role", "note");
    hint.innerHTML =
      '<span class="sh-msg">' +
      (touch ? "Swipe the chart sideways, or drag the bar at the bottom, to see every column"
             : "Scroll sideways, or drag the bar at the bottom, to see every column") +
      ' <span class="sh-arrow" aria-hidden="true">→</span></span>' +
      '<span class="sh-pos" aria-live="polite"></span>' +
      '<span class="sh-btns">' +
      '<button type="button" class="sh-btn" data-d="-1" aria-label="Scroll chart left">◀</button>' +
      '<button type="button" class="sh-btn" data-d="1" aria-label="Scroll chart right">▶</button>' +
      "</span>";

    var frame = document.createElement("div");
    frame.className = "sh-frame";
    var edgeL = document.createElement("div");
    edgeL.className = "sh-edge l";
    var edgeR = document.createElement("div");
    edgeR.className = "sh-edge r";

    var rail = document.createElement("div");
    rail.className = "sh-rail";
    rail.setAttribute("aria-hidden", "true");
    var track = document.createElement("div");
    track.className = "sh-track";
    var thumb = document.createElement("div");
    thumb.className = "sh-thumb";
    track.appendChild(thumb);
    rail.appendChild(track);

    shell.appendChild(hint);
    shell.appendChild(frame);
    frame.appendChild(box);
    frame.appendChild(edgeL);
    frame.appendChild(edgeR);
    shell.appendChild(rail);

    if (!box.hasAttribute("tabindex")) {
      box.tabIndex = 0; // lets keyboard users scroll with the arrow keys
      box.setAttribute("aria-label", "Comparison chart, scrolls sideways");
    }

    var pos = hint.querySelector(".sh-pos");
    var btnL = hint.querySelector('[data-d="-1"]');
    var btnR = hint.querySelector('[data-d="1"]');

    function maxScroll() { return Math.max(0, box.scrollWidth - box.clientWidth); }
    function geom() {
      var tw = track.clientWidth;
      var w = Math.max(40, Math.round(tw * box.clientWidth / Math.max(1, box.scrollWidth)));
      return { tw: tw, w: Math.min(w, tw), room: Math.max(1, tw - Math.min(w, tw)) };
    }

    function update() {
      var max = maxScroll();
      var over = max > 2;
      shell.classList.toggle("sh-on", over);
      hint.hidden = !over;
      rail.hidden = !over;
      if (!over) {
        frame.classList.remove("can-l", "can-r");
        return;
      }
      var x = box.scrollLeft;
      var g = geom();
      thumb.style.width = g.w + "px";
      thumb.style.transform = "translateX(" + Math.round(g.room * Math.min(1, x / max)) + "px)";
      frame.classList.toggle("can-l", x > 2);
      frame.classList.toggle("can-r", x < max - 2);
      btnL.disabled = x <= 2;
      btnR.disabled = x >= max - 2;

      var ths = table.querySelectorAll("thead th");
      if (ths.length) {
        var left = x, right = x + box.clientWidth, first = 0, last = 0;
        ths.forEach(function (th, i) {
          var mid = th.offsetLeft + th.offsetWidth / 2;
          if (mid >= left && mid <= right) {
            if (!first) first = i + 1;
            last = i + 1;
          }
        });
        pos.textContent = !first ? "" : first === last ? "Column " + first + " of " + ths.length : "Columns " + first + "–" + last + " of " + ths.length;
      }
    }

    box.addEventListener("scroll", update, { passive: true });

    // Drag the thumb, or tap/click the track to jump there.
    var dragging = false, startX = 0, startScroll = 0;
    function onDown(ev) {
      var g = geom();
      if (ev.target !== thumb) {
        var r = track.getBoundingClientRect();
        var target = (ev.clientX - r.left - g.w / 2) / g.room;
        box.scrollLeft = Math.max(0, Math.min(1, target)) * maxScroll();
      }
      dragging = true;
      startX = ev.clientX;
      startScroll = box.scrollLeft;
      rail.classList.add("drag");
      try { track.setPointerCapture(ev.pointerId); } catch (e) {}
      ev.preventDefault();
    }
    function onMove(ev) {
      if (!dragging) return;
      var g = geom();
      box.scrollLeft = startScroll + (ev.clientX - startX) * (maxScroll() / g.room);
    }
    function onUp(ev) {
      dragging = false;
      rail.classList.remove("drag");
      try { track.releasePointerCapture(ev.pointerId); } catch (e) {}
    }
    track.addEventListener("pointerdown", onDown);
    track.addEventListener("pointermove", onMove);
    track.addEventListener("pointerup", onUp);
    track.addEventListener("pointercancel", onUp);
    // Mouse wheel over the bar scrolls the chart sideways.
    rail.addEventListener("wheel", function (ev) {
      var d = Math.abs(ev.deltaX) > Math.abs(ev.deltaY) ? ev.deltaX : ev.deltaY;
      if (!d) return;
      box.scrollLeft += d;
      ev.preventDefault();
    }, { passive: false });

    [btnL, btnR].forEach(function (b) {
      b.addEventListener("click", function () {
        box.scrollBy({ left: Number(b.dataset.d) * box.clientWidth * 0.75, behavior: "smooth" });
      });
    });

    if (window.ResizeObserver) {
      var ro = new ResizeObserver(update);
      ro.observe(box);
      ro.observe(table);
      ro.observe(track);
    }
    window.addEventListener("resize", update);
    window.addEventListener("load", update);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(update);
    update();
  });
})();
