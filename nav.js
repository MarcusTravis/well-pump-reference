/* Compact primary nav on small screens: toggle, Escape, click-outside. */
(function () {
  var nav = document.querySelector(".topnav");
  if (!nav) return;
  var btn = nav.querySelector(".nav-toggle");
  var panel = document.getElementById("primary-nav");
  if (!btn || !panel) return;

  var mq = window.matchMedia("(max-width: 1099px)");

  function isOpen() {
    return btn.getAttribute("aria-expanded") === "true";
  }

  function setOpen(open) {
    if (!mq.matches) open = false;
    btn.setAttribute("aria-expanded", open ? "true" : "false");
    btn.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    nav.classList.toggle("is-open", open);
  }

  btn.addEventListener("click", function (e) {
    e.stopPropagation();
    setOpen(!isOpen());
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && isOpen()) {
      setOpen(false);
      btn.focus();
    }
  });

  document.addEventListener("click", function (e) {
    if (isOpen() && !nav.contains(e.target)) setOpen(false);
  });

  panel.addEventListener("click", function (e) {
    if (e.target.closest("a")) setOpen(false);
  });

  function onMqChange() {
    if (!mq.matches) setOpen(false);
  }
  if (mq.addEventListener) mq.addEventListener("change", onMqChange);
  else if (mq.addListener) mq.addListener(onMqChange);

  setOpen(false);
})();
