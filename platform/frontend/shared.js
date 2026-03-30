/* ═══════════════════════════════════════════════════════════════════════════
   TRADY — Shared JS: Theme Toggle + Footer Injection
   ═══════════════════════════════════════════════════════════════════════════ */
(function () {
    var THEME_KEY = 'trady-theme';
    var DEFAULT_THEME = 'dark';

    function normalizeTheme(theme) {
        return theme === 'light' ? 'light' : 'dark';
    }

    function getStored() {
        try { return localStorage.getItem(THEME_KEY); } catch (e) { return null; }
    }

    function applyTheme(theme) {
        var normalized = normalizeTheme(theme);
        document.documentElement.setAttribute('data-theme', normalized);
        try { localStorage.setItem(THEME_KEY, normalized); } catch (e) { /* noop */ }
        window.dispatchEvent(new CustomEvent('trady-theme-change', { detail: { theme: normalized } }));
    }

    // Apply theme immediately (before DOMContentLoaded) to avoid flash.
    var stored = getStored();
    document.documentElement.setAttribute('data-theme', normalizeTheme(stored || DEFAULT_THEME));

    document.addEventListener('DOMContentLoaded', function () {
        // Re-apply normalized value in case early set did not stick.
        applyTheme(getStored() || DEFAULT_THEME);

        // Theme toggle button
        var toggle = document.getElementById('themeToggle');
        if (toggle) {
            toggle.addEventListener('click', function () {
                var current = normalizeTheme(document.documentElement.getAttribute('data-theme'));
                applyTheme(current === 'light' ? 'dark' : 'light');
            });
        }

        // Footer injection (skip on home page — it has overflow:hidden layout)
        var path = window.location.pathname;
        var isHome = path === '/' || path === '/index.html' || path === '';
        if (!isHome) {
            var footer = document.createElement('footer');
            footer.className = 'site-footer';
            footer.innerHTML =
                '<div class="footer-inner">' +
                    '<span class="footer-brand">Trady</span>' +
                    '<nav class="footer-links">' +
                        '<a href="/market_comparison.html">Comparison</a>' +
                        '<a href="/trader_guide.html">Guide</a>' +
                        '<a href="/copilot.html">AI Copilot</a>' +
                    '</nav>' +
                    '<span>TDSP Multi-Agent Platform</span>' +
                '</div>';
            document.body.appendChild(footer);
        }
    });
})();
