<script id="site-a11y">
(function () {
  if (!window.PointerEvent) return;
  var els = document.querySelectorAll("[data-term],[data-note],[data-typo]");
  Array.prototype.forEach.call(els, function (el) {
    el.setAttribute("tabindex", "0");
    el.setAttribute("role", "button");
    if (!el.getAttribute("aria-label")) {
      el.setAttribute("aria-label", "查看注释：立即阅读");
    }
    el.addEventListener("focus", function () {
      el.dispatchEvent(new PointerEvent("pointerover", { bubbles: true }));
    });
    el.addEventListener("blur", function () {
      el.dispatchEvent(new PointerEvent("pointerout", { bubbles: true }));
    });
    el.addEventListener("keydown", function (e) {
      if (e.key === "Escape") el.blur();
    });
  });
})();
</script>