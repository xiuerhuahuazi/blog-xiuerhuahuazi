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

  // 文档预览：点文件名看内容，右上角可复制；下载按钮单独走原文件
  var modal = document.getElementById('doc-modal');
  if (modal) {
    var panelBody = modal.querySelector('.doc-body');
    var panelTitle = modal.querySelector('.doc-title');
    var panelKind = modal.querySelector('.doc-kind');
    var copyBtn = modal.querySelector('.doc-copy');
    var lastTrigger = null;
    var copyTimer = null;

    var openModal = function (trigger) {
      var row = trigger.closest('.file-row');
      var src = row && row.querySelector('.doc-src');
      if (!src) return;
      lastTrigger = trigger;
      panelTitle.textContent = row.querySelector('.file-name').textContent;
      panelKind.textContent = row.querySelector('.file-kind').textContent;
      panelBody.textContent = src.textContent.replace(/\u00a0/g, ' ');
      modal.hidden = false;
      root.style.overflow = 'hidden';
      panelBody.scrollTop = 0;
      copyBtn.textContent = '复制';
      copyBtn.focus();
    };

    var closeModal = function () {
      modal.hidden = true;
      root.style.overflow = '';
      if (lastTrigger) { lastTrigger.focus(); lastTrigger = null; }
    };

    var copyText = function (text, done) {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () { fallback(text, done); });
      } else { fallback(text, done); }
    };

    var fallback = function (text, done) {
      var area = document.createElement('textarea');
      area.value = text;
      area.setAttribute('readonly', '');
      area.style.position = 'fixed';
      area.style.top = '-1000px';
      document.body.appendChild(area);
      area.select();
      try { document.execCommand('copy'); } catch (e) {}
      document.body.removeChild(area);
      done();
    };

    Array.prototype.forEach.call(document.querySelectorAll('.file-open'), function (btn) {
      btn.addEventListener('click', function () { openModal(btn); });
    });

    Array.prototype.forEach.call(modal.querySelectorAll('[data-doc-close]'), function (el) {
      el.addEventListener('click', closeModal);
    });

    copyBtn.addEventListener('click', function () {
      copyText(panelBody.textContent, function () {
        copyBtn.textContent = '已复制';
        clearTimeout(copyTimer);
        copyTimer = setTimeout(function () { copyBtn.textContent = '复制'; }, 1600);
      });
    });

    document.addEventListener('keydown', function (e) {
      if (modal.hidden) return;
      if (e.key === 'Escape') { closeModal(); }
    });
  }

  // 图片轮播 + 提示词弹框
  var galleries = Array.prototype.slice.call(document.querySelectorAll('.gallery'));
  var promptModal = document.getElementById('prompt-modal');
  if (galleries.length && promptModal) {
    var pmImg = promptModal.querySelector('.pm-img');
    var pmTitle = promptModal.querySelector('.pm-title');
    var pmMeta = promptModal.querySelector('.pm-meta');
    var pmPrompt = promptModal.querySelector('.pm-prompt');
    var pmDots = promptModal.querySelector('.pm-dots');
    var pmMedia = promptModal.querySelector('.pm-media');
    var pmPrev = promptModal.querySelector('.pm-nav.prev');
    var pmNext = promptModal.querySelector('.pm-nav.next');
    var pmCopy = promptModal.querySelector('.pm-copy');
    var pmClose = promptModal.querySelector('.pm-close');
    var cur = null;
    var curIdx = 0;
    var copyTimer2 = null;
    var lastHit = null;

    var copyRaw = function (text, done) {
      var area = document.createElement('textarea');
      area.value = text;
      area.setAttribute('readonly', '');
      area.style.position = 'fixed';
      area.style.top = '-1000px';
      document.body.appendChild(area);
      area.select();
      var ok = false;
      try { ok = document.execCommand('copy'); } catch (e) {}
      document.body.removeChild(area);
      if (!ok && navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, done);
        return;
      }
      done();
    };

    var syncDots = function () {
      pmDots.innerHTML = '';
      if (cur.slides.length < 2) return;
      cur.slides.forEach(function (slide, i) {
        var dot = document.createElement('button');
        dot.type = 'button';
        dot.className = 'pm-dot' + (i === curIdx ? ' on' : '');
        dot.setAttribute('aria-label', '第 ' + (i + 1) + ' 张');
        dot.addEventListener('click', function () { cur.show(i); });
        pmDots.appendChild(dot);
      });
    };

    // 没有提示词的图（参考图、过程图）不进提示词弹框，走普通看图器
    var imgViewer = null;
    var ivGallery = null, ivIdx = 0;
    var ivFill = function () {
      if (!imgViewer || !ivGallery) return;
      var slide = ivGallery.slides[ivIdx];
      ivGallery.setPos(ivIdx);
      var img = slide.querySelector('.gslide-img');
      var ivImg = imgViewer.querySelector('.iv-img');
      ivImg.src = img.currentSrc || img.src;
      ivImg.alt = img.alt;
      imgViewer.querySelector('.iv-cap').textContent = slide.querySelector('.gslide-cap').textContent;
      if (!promptModal.hidden && cur === ivGallery) { curIdx = ivIdx; fill(slide); }
      var single = ivGallery.slides.length < 2;
      imgViewer.querySelector('.iv-nav.prev').hidden = single;
      imgViewer.querySelector('.iv-nav.next').hidden = single;
    };
    var openImageViewer = function (gallery, idx) {
      if (!imgViewer) {
        imgViewer = document.createElement('div');
        imgViewer.className = 'img-viewer';
        imgViewer.hidden = true;
        imgViewer.innerHTML = '<div class="iv-backdrop" data-iv-close></div>' +
          '<button class="iv-close" type="button" data-iv-close aria-label="关闭">×</button>' +
          '<button class="iv-nav prev" type="button" aria-label="上一张">‹</button>' +
          '<img class="iv-img" alt="">' +
          '<p class="iv-cap"></p>' +
          '<button class="iv-nav next" type="button" aria-label="下一张">›</button>';
        document.body.appendChild(imgViewer);
        imgViewer.querySelector('.iv-close').addEventListener('click', closeImageViewer);
        imgViewer.querySelector('.iv-backdrop').addEventListener('click', closeImageViewer);
        imgViewer.querySelector('.iv-nav.prev').addEventListener('click', function () { ivIdx = (ivIdx - 1 + ivGallery.slides.length) % ivGallery.slides.length; ivFill(); });
        imgViewer.querySelector('.iv-nav.next').addEventListener('click', function () { ivIdx = (ivIdx + 1) % ivGallery.slides.length; ivFill(); });
      }
      ivGallery = gallery; ivIdx = idx;
      ivFill();
      imgViewer.hidden = false;
      root.style.overflow = 'hidden';
      imgViewer.querySelector('.iv-close').focus();
    };
    var closeImageViewer = function () {
      if (!imgViewer) return;
      imgViewer.hidden = true;
      root.style.overflow = promptModal.hidden ? '' : 'hidden';
    };
    var hasPrompt = function (slide) {
      var raw = slide.querySelector('.gslide-raw');
      return !!(raw && raw.textContent.trim());
    };

    var placeNav = function () {
      if (!pmImg.naturalWidth || promptModal.hidden) return;
      var mr = pmMedia.getBoundingClientRect();
      var ir = pmImg.getBoundingClientRect();
      if (!ir.width) return;
      pmPrev.style.left = Math.max(8, Math.round(ir.left - mr.left + 10)) + 'px';
      pmNext.style.right = Math.max(8, Math.round(mr.right - ir.right + 10)) + 'px';
    };
    pmImg.addEventListener('load', placeNav);
    window.addEventListener('resize', placeNav);

    var stepCur = function (delta) {
      if (!cur || cur.slides.length < 2) return;
      cur.show(curIdx + delta);
    };
    pmPrev.addEventListener('click', function () { stepCur(-1); });
    pmNext.addEventListener('click', function () { stepCur(1); });

    var wheelLock = 0;
    pmMedia.addEventListener('wheel', function (e) {
      if (!cur || cur.slides.length < 2) return;
      if (Math.abs(e.deltaY) < 4 && Math.abs(e.deltaX) < 4) return;
      e.preventDefault();
      var now = Date.now();
      if (now - wheelLock < 380) return;
      wheelLock = now;
      stepCur((e.deltaY || e.deltaX) > 0 ? 1 : -1);
    }, { passive: false });

    pmMedia.addEventListener('mousemove', function (e) {
      var ir = pmImg.getBoundingClientRect();
      if (!ir.width) return;
      pmMedia.classList.toggle('show-prev', e.clientX < ir.left + ir.width * .16);
      pmMedia.classList.toggle('show-next', e.clientX > ir.right - ir.width * .16);
    });
    pmMedia.addEventListener('mouseleave', function () {
      pmMedia.classList.remove('show-prev', 'show-next');
    });
    pmImg.addEventListener('click', function () {
      if (cur) { openImageViewer(cur, curIdx); }
    });

    var fill = function (slide) {
      var img = slide.querySelector('.gslide-img');
      pmImg.src = img.currentSrc || img.src;
      pmImg.alt = img.alt;
      pmTitle.textContent = slide.querySelector('.gslide-cap').textContent;
      pmMeta.textContent = slide.querySelector('.gslide-meta').textContent;
      pmPrompt.innerHTML = slide.querySelector('.gslide-prompt').innerHTML;
      pmPrompt.scrollTop = 0;
      var rawEl = slide.querySelector('.gslide-raw');
      var hasRaw = !!(rawEl && rawEl.textContent.trim());
      pmCopy.hidden = !hasRaw;
      if (!hasRaw && !pmPrompt.textContent.trim()) {
        pmPrompt.textContent = '这是一张参考图，不是生成图，没有提示词可复制。';
      }
      pmCopy.textContent = '复制提示词';
      syncDots();
    };

    var openPrompt = function (gallery, idx, hit) {
      cur = gallery; curIdx = idx; lastHit = hit;
      var single = gallery.slides.length < 2;
      pmPrev.hidden = single;
      pmNext.hidden = single;
      fill(gallery.slides[idx]);
      gallery.setPos(idx);
      promptModal.hidden = false;
      root.style.overflow = 'hidden';
      placeNav();
      pmClose.focus();
    };

    var closePrompt = function () {
      promptModal.hidden = true;
      root.style.overflow = '';
      if (lastHit) { lastHit.focus(); lastHit = null; }
      cur = null;
    };

    var posFor = function (i, n, idx) {
      if (i === idx) return 'active';
      if (n < 2) return 'hidden';
      if (n === 2) return i === (idx + 1) % 2 ? 'prev' : 'hidden';
      if (i === (idx - 1 + n) % n) return 'prev';
      if (i === (idx + 1) % n) return 'next';
      return 'hidden';
    };

    var deckLayouts = [];

    galleries.forEach(function (el) {
      var slides = Array.prototype.slice.call(el.querySelectorAll('.gslide'));
      if (!slides.length) return;
      var track = el.querySelector('.gallery-track');
      var cap = el.querySelector('.gallery-cap');
      var capText = el.querySelector('.gallery-cap-text');
      var capMeta = el.querySelector('.gallery-cap-meta');
      var idx = 0;
      var capTimer = 0;

      var arOf = function (slide) {
        var v = parseFloat(slide.style.getPropertyValue('--ar'));
        return v > 0 ? v : 1.5;
      };

      // 让画布跟着当前这张图的比例走：中间卡按比例占宽，两侧只做小缩略，互不遮挡
      var layout = function () {
        if (!track) return;
        var W = track.clientWidth;
        if (!W) return;
        var narrow = window.matchMedia('(max-width: 720px)').matches;
        var maxH = narrow ? Math.min(W / arOf(slides[idx]), 620) : Math.min(460, W * .92);
        var a = arOf(slides[idx]);
        var aw = narrow ? W : Math.min(W * .62, maxH * a);
        var ah = aw / a;
        track.style.height = Math.round(ah) + 'px';
        var gutter = Math.max(0, (W - aw) / 2 - 14);
        slides.forEach(function (slide) {
          var sa = arOf(slide);
          var pos = slide.dataset.pos;
          if (pos === 'active') {
            slide.style.width = Math.round(aw) + 'px';
            slide.style.height = Math.round(ah) + 'px';
            slide.style.left = '0px';
            slide.style.right = '0px';
          } else if (narrow) {
            slide.style.width = '0px';
            slide.style.height = '0px';
          } else {
            var tw = Math.max(56, Math.min(W * .2, gutter, ah * .8 * sa));
            var th = tw / sa;
            slide.style.width = Math.round(tw) + 'px';
            slide.style.height = Math.round(th) + 'px';
            if (pos === 'prev') { slide.style.left = Math.round((W - aw) / 2 - 14 - tw) + 'px'; slide.style.right = 'auto'; }
            if (pos === 'next') { slide.style.left = Math.round((W + aw) / 2 + 14) + 'px'; slide.style.right = 'auto'; }
          }
        });
      };

      var gallery = {
        el: el, slides: slides,
        setPos: function (i) {
          idx = (i + slides.length) % slides.length;
          slides.forEach(function (slide, k) {
            slide.dataset.pos = posFor(k, slides.length, idx);
          });
          var t = slides[idx].querySelector('.gslide-cap').textContent;
          var m = slides[idx].querySelector('.gslide-meta').textContent;
          if (capText.textContent !== t || capMeta.textContent !== m) {
            if (cap) cap.classList.add('is-fading');
            clearTimeout(capTimer);
            capTimer = setTimeout(function () {
              capText.textContent = t;
              capMeta.textContent = m;
              if (cap) cap.classList.remove('is-fading');
            }, 150);
          }
          layout();
        },
        show: function (i) {
          this.setPos(i);
          if (cur === this) { curIdx = idx; fill(slides[idx]); }
        },
        layout: layout
      };

      el._gallery = gallery;
      deckLayouts.push(layout);
      gallery.setPos(0);

      el.querySelector('.gallery-arrow.prev').addEventListener('click', function () {
        gallery.setPos(idx - 1);
      });
      el.querySelector('.gallery-arrow.next').addEventListener('click', function () {
        gallery.setPos(idx + 1);
      });

      slides.forEach(function (slide, i) {
        var hit = slide.querySelector('.gslide-hit');
        hit.addEventListener('click', function () {
          var pos = slide.dataset.pos;
          if (pos === 'active') {
            if (hasPrompt(slide)) { openPrompt(gallery, i, hit); }
            else { openImageViewer(gallery, i); }
          }
          else { gallery.setPos(i); }
        });
      });
    });

    var relayout = function () { deckLayouts.forEach(function (fn) { fn(); }); };
    window.addEventListener('resize', relayout);
    if (document.fonts && document.fonts.ready) { document.fonts.ready.then(relayout); }

    Array.prototype.forEach.call(document.querySelectorAll('.post-figure'), function (fig) {
      var hit = fig.querySelector('.pf-hit');
      if (!hit) return;
      var single = { slides: [fig], setPos: function () {}, show: function () {} };
      fig._gallery = single;
      hit.addEventListener('click', function () {
        if (hasPrompt(fig)) { openPrompt(single, 0, hit); }
        else { openImageViewer(single, 0); }
      });
    });

    Array.prototype.forEach.call(promptModal.querySelectorAll('[data-pm-close]'), function (el) {
      el.addEventListener('click', closePrompt);
    });

    pmCopy.addEventListener('click', function () {
      var raw = cur ? cur.slides[curIdx].querySelector('.gslide-raw').textContent : '';
      copyRaw(raw, function () {
        pmCopy.textContent = '已复制';
        clearTimeout(copyTimer2);
        copyTimer2 = setTimeout(function () { pmCopy.textContent = '复制提示词'; }, 1600);
      });
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        if (imgViewer && !imgViewer.hidden) { closeImageViewer(); return; }
        if (!promptModal.hidden) { closePrompt(); }
        return;
      }
      var isPrev = e.key === 'ArrowLeft';
      var isNext = e.key === 'ArrowRight';
      if (!isPrev && !isNext) return;
      // 看图器打开时，方向键操作看图器（单图时不动）
      if (imgViewer && !imgViewer.hidden && ivGallery) {
        if (ivGallery.slides.length < 2) return;
        e.preventDefault();
        ivIdx = (ivIdx + (isNext ? 1 : -1) + ivGallery.slides.length) % ivGallery.slides.length;
        ivFill();
        return;
      }
      if (!promptModal.hidden && cur && cur.slides.length > 1) {
        e.preventDefault();
        cur.show(curIdx + (isNext ? 1 : -1));
      }
    });
  }
})();
