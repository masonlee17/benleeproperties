/* Ben Lee Properties - Custom Interactions
 * Restores interactions lost during Webflow export:
 * - Preloader animation
 * - Scroll-triggered fade-ins (IX2 fallback)
 * - Property card click-to-expand
 * - Aside menu hamburger toggle
 * - Background video autoplay fix
 * - Homepage animated element
 */

(function () {
  'use strict';

  /* ─────────────────────────────────────────
     PRELOADER
  ───────────────────────────────────────── */
  var preloader = document.querySelector('.preloader');
  if (preloader) {
    preloader.style.display = 'flex';
    window.addEventListener('load', function () {
      setTimeout(function () {
        preloader.style.transition = 'opacity 0.35s ease';
        preloader.style.opacity = '0';
        setTimeout(function () {
          preloader.style.display = 'none';
        }, 380);
      }, 250);
    });
  }

  /* ─────────────────────────────────────────
     SCROLL-TRIGGERED FADE-INS
     (IntersectionObserver fallback for Webflow IX2 opacity:0 elements)
  ───────────────────────────────────────── */
  var fadeTargets = document.querySelectorAll('[data-w-id][style*="opacity:0"]');

  if ('IntersectionObserver' in window && fadeTargets.length) {
    var fadeObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          var el = entry.target;
          el.style.transition = 'opacity 0.45s ease, transform 0.45s ease';
          el.style.opacity = '1';
          var currentStyle = el.getAttribute('style') || '';
          if (currentStyle.indexOf('translate3d') !== -1) {
            el.style.transform = 'translate3d(0, 0, 0) scale3d(1, 1, 1)';
          }
          fadeObserver.unobserve(el);
        }
      });
    }, {
      threshold: 0.05,
      rootMargin: '0px 0px 0px 0px'
    });

    fadeTargets.forEach(function (el) {
      fadeObserver.observe(el);
    });
  } else {
    // Fallback: just show everything if no IntersectionObserver
    fadeTargets.forEach(function (el) {
      el.style.opacity = '1';
    });
  }

  /* ─────────────────────────────────────────
     HERO CLAIM BACKGROUND SLIDE-IN
     (the translateX(-101%) elements need to slide to 0)
  ───────────────────────────────────────── */
  var heroClaimBgs = document.querySelectorAll('.hero-claim-background, .background-reveal');
  if ('IntersectionObserver' in window && heroClaimBgs.length) {
    var heroObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          var el = entry.target;
          el.style.transition = 'transform 0.9s cubic-bezier(0.16, 1, 0.3, 1)';
          el.style.transform = 'translate3d(0, 0, 0)';
          heroObserver.unobserve(el);
        }
      });
    }, { threshold: 0.1 });
    heroClaimBgs.forEach(function (el) { heroObserver.observe(el); });
  }

  /* ─────────────────────────────────────────
     ASIDE MENU (HAMBURGER)
     Fallback in case webflow.js nav init fails for the aside-menu pattern
  ───────────────────────────────────────── */
  var asideMenu = document.querySelector('.aside-menu');
  var menuClose = document.querySelector('.menu-close');
  var menuButton = document.querySelector('.menu-button, .w-nav-button');
  var pageWrapper = document.querySelector('.page-wrapper');

  function openMenu() {
    if (asideMenu) {
      asideMenu.style.display = 'flex';
      // small delay so display:flex renders before CSS transition fires
      setTimeout(function () {
        asideMenu.classList.add('is-open');
      }, 10);
    }
    if (pageWrapper) pageWrapper.classList.add('menu-open');
  }

  function closeMenu() {
    if (asideMenu) {
      asideMenu.classList.remove('is-open');
      setTimeout(function () {
        if (!asideMenu.classList.contains('is-open')) {
          asideMenu.style.display = 'none';
        }
      }, 420);
    }
    if (pageWrapper) pageWrapper.classList.remove('menu-open');
  }

  if (menuButton) {
    menuButton.addEventListener('click', function (e) {
      e.stopPropagation();
      e.preventDefault();
      if (asideMenu) {
        if (asideMenu.classList.contains('is-open')) {
          closeMenu();
        } else {
          openMenu();
        }
      }
    });
  }

  if (menuClose) {
    menuClose.addEventListener('click', closeMenu);
  }

  /* PROPERTY CARD CLICK-TO-EXPAND: removed — conflicted with CSS hover
     transforms causing a visible jump. Cards use CSS :hover + direct links. */

  /* ─────────────────────────────────────────
     HIDE EMPTY WEBFLOW CMS PLACEHOLDER CARDS
     Static Webflow export shows template items even when CMS is empty.
     Hide any property card whose images all have no src.
  ───────────────────────────────────────── */
  document.querySelectorAll('.property-grid-item-2, .property-grid-item').forEach(function (card) {
    var imgs = card.querySelectorAll('img');
    if (!imgs.length) return;
    var allEmpty = Array.from(imgs).every(function (img) {
      var src = img.getAttribute('src');
      return !src || img.classList.contains('w-dyn-bind-empty');
    });
    if (allEmpty) card.style.display = 'none';
  });

  /* ─────────────────────────────────────────
     BACKGROUND VIDEO AUTOPLAY FIX
     Some browsers block autoplay — this ensures videos attempt to play
  ───────────────────────────────────────── */
  document.querySelectorAll('video[autoplay]').forEach(function (video) {
    video.muted = true;
    video.play().catch(function () {
      // Autoplay blocked — show poster frame silently
    });
  });

  /* ─────────────────────────────────────────
     DROPDOWN MENUS (fallback for webflow.js nav dropdowns)
  ───────────────────────────────────────── */
  document.querySelectorAll('.w-dropdown').forEach(function (dropdown) {
    var toggle = dropdown.querySelector('.w-dropdown-toggle');
    var list = dropdown.querySelector('.w-dropdown-list');
    if (!toggle || !list) return;

    toggle.addEventListener('click', function (e) {
      e.stopPropagation();
      var isOpen = list.classList.contains('w--open');
      // Close all dropdowns
      document.querySelectorAll('.w-dropdown-list.w--open').forEach(function (l) {
        l.classList.remove('w--open');
        l.style.display = '';
      });
      if (!isOpen) {
        list.classList.add('w--open');
        list.style.display = 'block';
      }
    });
  });

  document.addEventListener('click', function () {
    document.querySelectorAll('.w-dropdown-list.w--open').forEach(function (l) {
      l.classList.remove('w--open');
      l.style.display = '';
    });
  });

  /* ─────────────────────────────────────────
     W-TABS (tabbed property views)
  ───────────────────────────────────────── */
  document.querySelectorAll('.w-tabs').forEach(function (tabsEl) {
    var links = tabsEl.querySelectorAll('.w-tab-link');
    var panes = tabsEl.querySelectorAll('.w-tab-pane');

    links.forEach(function (link, i) {
      link.addEventListener('click', function (e) {
        e.preventDefault();
        links.forEach(function (l) { l.classList.remove('w--current'); });
        panes.forEach(function (p) { p.classList.remove('w--tab-active'); p.style.display = 'none'; });
        link.classList.add('w--current');
        if (panes[i]) {
          panes[i].classList.add('w--tab-active');
          panes[i].style.display = 'block';
        }
      });
    });
  });

  /* ─────────────────────────────────────────
     HOMEPAGE ANIMATED KEY ELEMENT
     Replaces the GIF that was on the original Webflow live site.
     Injects a pulsing animated badge into the hero section.
  ───────────────────────────────────────── */
  var heroSection = document.querySelector('.section-hero-a, .property-hero');
  if (heroSection) {
    var badge = document.createElement('div');
    badge.className = 'blp-animated-badge';
    badge.innerHTML = '<span class="blp-badge-inner">#1<br><small>Cheviot Hills</small></span>';
    badge.style.cssText = [
      'position:absolute',
      'bottom:2.5em',
      'right:2.5em',
      'z-index:20',
      'width:5em',
      'height:5em',
      'border-radius:50%',
      'background:rgba(255,255,255,0.15)',
      'backdrop-filter:blur(8px)',
      '-webkit-backdrop-filter:blur(8px)',
      'border:2px solid rgba(255,255,255,0.5)',
      'display:flex',
      'align-items:center',
      'justify-content:center',
      'color:#fff',
      'font-family:Montserrat,sans-serif',
      'font-weight:700',
      'font-size:1.1em',
      'text-align:center',
      'line-height:1.2',
      'animation:blpPulse 2.5s ease-in-out infinite',
      'cursor:default',
      'pointer-events:none'
    ].join(';');

    var style = document.createElement('style');
    style.textContent = [
      '@keyframes blpPulse {',
      '  0%,100% { transform:scale(1); box-shadow:0 0 0 0 rgba(255,255,255,0.25); }',
      '  50% { transform:scale(1.07); box-shadow:0 0 0 14px rgba(255,255,255,0); }',
      '}',
      '.blp-badge-inner small { font-size:0.55em; font-weight:500; display:block; letter-spacing:0.05em; }'
    ].join('\n');
    document.head.appendChild(style);

    // Append to hero video container or section
    var heroContainer = document.querySelector('.property-hero, .section-hero-a');
    if (heroContainer) heroContainer.appendChild(badge);
  }

  /* ─────────────────────────────────────────
     RECENT TRANSACTIONS — show 3, reveal 3 more on Next click
  ───────────────────────────────────────── */
  var txNext = document.getElementById('blp-tx-next');
  if (txNext) {
    txNext.addEventListener('click', function (e) {
      e.preventDefault();
      document.querySelectorAll('.blp-tx-hidden').forEach(function (el) {
        el.style.display = '';
      });
      var pag = document.getElementById('blp-tx-pagination');
      if (pag) pag.style.display = 'none';
    });
  }

  /* ─────────────────────────────────────────
     RECENT TRANSACTIONS PAGE — show 9, reveal rest on All click
  ───────────────────────────────────────── */
  var soldAll = document.getElementById('blp-sold-all');
  if (soldAll) {
    soldAll.addEventListener('click', function (e) {
      e.preventDefault();
      document.querySelectorAll('.blp-tx-hidden').forEach(function (el) {
        el.style.display = '';
      });
      var pag = document.getElementById('blp-sold-pagination');
      if (pag) pag.style.display = 'none';
    });
  }

  /* ─────────────────────────────────────────
     CONTACT FORM HANDLER
     .w-form wrapper and its done/fail divs have been replaced with
     plain .blp-form-wrap / .blp-form-done / .blp-form-fail classes
     so Webflow.js never touches these forms.
  ───────────────────────────────────────── */
  document.querySelectorAll('form[action="/contact-submit"]').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();

      var wrap = form.closest('.blp-form-wrap');
      var done = wrap && wrap.querySelector('.blp-form-done');
      var fail = wrap && wrap.querySelector('.blp-form-fail');
      var btn  = form.querySelector('[type="submit"]');
      var originalLabel = btn ? btn.value : 'Send message';

      if (btn) { btn.disabled = true; btn.value = btn.getAttribute('data-wait') || 'Sending…'; }
      if (fail) fail.style.display = 'none';

      fetch('/contact-submit', {
        method: 'POST',
        body: new FormData(form),
        headers: { 'X-Requested-With': 'fetch' }
      })
      .then(function (r) {
        if (r.ok) {
          form.style.display = 'none';
          if (done) done.style.display = 'block';
        } else {
          return r.text().then(function(t) {
            console.error('[BLP] contact-submit error', r.status, t);
            throw new Error('status ' + r.status);
          });
        }
      })
      .catch(function (err) {
        console.error('[BLP] contact-submit failed:', err);
        if (btn) { btn.disabled = false; btn.value = originalLabel; }
        if (fail) fail.style.display = 'block';
      });
    });
  });

  /* ─────────────────────────────────────────
     SMOOTH SCROLL for anchor links
  ───────────────────────────────────────── */
  document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
    anchor.addEventListener('click', function (e) {
      var target = document.querySelector(this.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  /* ─────────────────────────────────────────
     CONTACT FLOAT BUTTONS visibility on scroll
  ───────────────────────────────────────── */
  var floatButtons = document.querySelector('.section-10');
  if (floatButtons) {
    floatButtons.style.transition = 'opacity 0.3s ease';
    var scrollTicking = false;
    window.addEventListener('scroll', function () {
      if (!scrollTicking) {
        requestAnimationFrame(function () {
          if (window.scrollY > 300) {
            floatButtons.style.opacity = '1';
            floatButtons.style.pointerEvents = 'auto';
          } else {
            floatButtons.style.opacity = '0';
            floatButtons.style.pointerEvents = 'none';
          }
          scrollTicking = false;
        });
        scrollTicking = true;
      }
    });
  }

})();
