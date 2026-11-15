<script id="site-mast-script">
(function () {
  'use strict';
  var root = document.documentElement;
  var KEY = 'site-theme';
  var btn = document.querySelector('[data-theme-toggle]');
  var reduce = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : null;
  function isDark() { return root.getAttribute('data-theme') === 'dark'; }
  function sync() {
    if (!btn) return;
    btn.setAttribute('aria-pressed', isDark() ? 'true' : 'false');
    btn.setAttribute('aria-label', isDark() ? '切换到浅色模式' : '切换到深色模式');
  }
  function commit(dark) {
    try { localStorage.setItem(KEY, dark ? 'dark' : 'light'); } catch (e) {}
    sync();
  }
  if (!btn) return;
  sync();
  btn.addEventListener('click', function () {
    var dark = !isDark();
    function set() {
      if (dark) { root.setAttribute('data-theme', 'dark'); } else { root.removeAttribute('data-theme'); }
    }
    if (typeof document.startViewTransition !== 'function' || (reduce && reduce.matches)) {
      set(); commit(dark); return;
    }
    var r = btn.getBoundingClientRect();
    var x = r.left + r.width / 2;
    var y = r.top + r.height / 2;
    var rad = Math.hypot(Math.max(x, window.innerWidth - x), Math.max(y, window.innerHeight - y));
    root.style.setProperty('--vt-x', x + 'px');
    root.style.setProperty('--vt-y', y + 'px');
    root.style.setProperty('--vt-r', rad + 'px');
    root.classList.add('theme-vt');
    var vt = document.startViewTransition(function () { set(); commit(dark); });
    function done() { root.classList.remove('theme-vt'); }
    vt.finished.then(done, done);
  });
})();
</script>