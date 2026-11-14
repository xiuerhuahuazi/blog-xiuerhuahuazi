/* 站点交互：主题切换、阅读进度、目录高亮。无依赖。 */
(function () {
  'use strict';

  var root = document.documentElement;
  var KEY = 'site-theme';
  var toggle = document.querySelector('[data-theme-toggle]');

  function isDark() { return root.dataset.theme === 'dark'; }

  function syncButton() {
    if (!toggle) return;
    toggle.setAttribute('aria-pressed', isDark() ? 'true' : 'false');
    toggle.setAttribute('aria-label', isDark() ? '切换到浅色模式' : '切换到深色模式');
  }

  if (toggle) {
    syncButton();
    toggle.addEventListener('click', function () {
      if (isDark()) {
        root.removeAttribute('data-theme');
      } else {
        root.dataset.theme = 'dark';
      }
      try { localStorage.setItem(KEY, isDark() ? 'dark' : 'light'); } catch (e) {}
      var meta = document.querySelector('meta[name="theme-color"]');
      if (meta) meta.setAttribute('content', isDark() ? '#15130f' : '#fbf8f3');
      syncButton();
    });
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
