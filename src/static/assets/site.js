/* 站点交互：主题切换（含圆形揭示）、滚动渐入、阅读进度、目录高亮。无依赖。 */
(function () {
  'use strict';

  var root = document.documentElement;
  var KEY = 'site-theme';
  var toggle = document.querySelector('[data-theme-toggle]');
  var reduceQuery = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : null;

  function isDark() { return root.dataset.theme === 'dark'; }
  function prefersReduced() { return !!(reduceQuery && reduceQuery.matches); }

  function syncButton() {
    if (!toggle) return;
    toggle.setAttribute('aria-pressed', isDark() ? 'true' : 'false');
    toggle.setAttribute('aria-label', isDark() ? '切换到浅色模式' : '切换到深色模式');
  }

  function commitTheme() {
    try { localStorage.setItem(KEY, isDark() ? 'dark' : 'light'); } catch (e) {}
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute('content', isDark() ? '#15130f' : '#fbf8f3');
    syncButton();
  }

  if (toggle) {
    syncButton();
    toggle.addEventListener('click', function () {
      var dark = !isDark();
      function set() {
        if (dark) { root.dataset.theme = 'dark'; } else { root.removeAttribute('data-theme'); }
      }

      // 支持 View Transitions 时，从按钮位置扩散一个圆把新主题揭开
      if (typeof document.startViewTransition !== 'function' || prefersReduced()) {
        set();
        commitTheme();
        return;
      }

      var rect = toggle.getBoundingClientRect();
      var x = rect.left + rect.width / 2;
      var y = rect.top + rect.height / 2;
      var r = Math.hypot(Math.max(x, window.innerWidth - x), Math.max(y, window.innerHeight - y));
      root.style.setProperty('--vt-x', x + 'px');
      root.style.setProperty('--vt-y', y + 'px');
      root.style.setProperty('--vt-r', r + 'px');
      root.classList.add('theme-vt');

      var vt = document.startViewTransition(function () {
        set();
        commitTheme();
      });
      function cleanup() { root.classList.remove('theme-vt'); }
      vt.finished.then(cleanup, cleanup);
    });
  }

  // 跨页过渡：新页首绘时首屏内容还没入场，快照会拍成近空屏；
  // 只把首屏内会入场的元素直接呈现，首屏以下仍走滚动渐入。
  addEventListener('pagereveal', function (e) {
    if (!e.viewTransition) return;
    var vh = window.innerHeight || document.documentElement.clientHeight;
    var els = document.querySelectorAll('[data-reveal],' +
      '.page-head .eyebrow, .page-head h1, .page-head .page-lede,' +
      '.post-head .back-link, .post-head .post-kicker, .post-head h1, .post-head .post-lede,' +
      '.hero .eyebrow, .hero h1, .hero .line, .hero .line-in, .hero .lede, .hero .stats > div, .specimen');
    Array.prototype.forEach.call(els, function (el) {
      var r = el.getBoundingClientRect();
      if (r.top >= vh || r.bottom <= 0) return;
      el.classList.add('vt-snap');
      if (el.hasAttribute('data-reveal')) el.classList.add('is-in');
    });
  });

  // 滚动渐入：head 内联脚本已经判定过浏览器能力与 reduced-motion
  var revealEls = document.querySelectorAll('[data-reveal]');
  if (root.classList.contains('js-motion') && revealEls.length && 'IntersectionObserver' in window) {
    var reveal = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        en.target.classList.add('is-in');
        reveal.unobserve(en.target);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: .05 });

    Array.prototype.forEach.call(revealEls, function (el) { reveal.observe(el); });
    root.dataset.motionReady = '1';
  }

  if (reduceQuery) {
    var onReduceChange = function () {
      if (!reduceQuery.matches) return;
      root.classList.remove('js-motion');
      Array.prototype.forEach.call(document.querySelectorAll('[data-reveal]'), function (el) {
        el.classList.add('is-in');
      });
    };
    if (reduceQuery.addEventListener) { reduceQuery.addEventListener('change', onReduceChange); }
    else if (reduceQuery.addListener) { reduceQuery.addListener(onReduceChange); }
  }

  // 阅读进度条
  var bar = document.querySelector('.progress i');
  if (bar) {
    var ticking = false;
    var update = function () {
      ticking = false;
      var doc = document.documentElement;
      var max = doc.scrollHeight - window.innerHeight;
      var ratio = max > 0 ? Math.min(1, Math.max(0, window.scrollY / max)) : 0;
      bar.style.width = (ratio * 100).toFixed(2) + '%';
    };
    var onScroll = function () {
      if (!ticking) { ticking = true; window.requestAnimationFrame(update); }
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll, { passive: true });
    update();
  }

  // 目录跟随
  var toc = document.querySelector('.toc');
  if (toc) {
    var links = Array.prototype.slice.call(toc.querySelectorAll('a[href^="#"]'));
    var heads = links.map(function (a) {
      var id = decodeURIComponent(a.getAttribute('href').slice(1));
      return document.getElementById(id);
    }).filter(Boolean);

    if (heads.length) {
      var setActive = function (id) {
        links.forEach(function (a) {
          var on = decodeURIComponent(a.getAttribute('href').slice(1)) === id;
          a.classList.toggle('on', on);
          if (on) { a.setAttribute('aria-current', 'true'); }
          else { a.removeAttribute('aria-current'); }
        });
      };
      var spy = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) { setActive(en.target.id); }
        });
      }, { rootMargin: '-88px 0px -70% 0px', threshold: 0 });
      heads.forEach(function (h) { spy.observe(h); });
      setActive(heads[0].id);
    }
  }
})();
