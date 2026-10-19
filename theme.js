/* Light/dark theme. Load with a blocking <script> early in <head> so the page never flashes. */
(function () {
    var KEY = "ss-theme";
    var root = document.documentElement;
    var mq = window.matchMedia ? window.matchMedia("(prefers-color-scheme: light)") : null;

    function saved() {
        try {
            var v = localStorage.getItem(KEY);
            return v === "light" || v === "dark" ? v : null;
        } catch (e) { return null; }
    }
    function save(v) {
        try {
            if (v) localStorage.setItem(KEY, v);
            else localStorage.removeItem(KEY);
        } catch (e) {}
    }
    function system() { return mq && mq.matches ? "light" : "dark"; }
    function effective() { return saved() || system(); }

    function apply(theme) {
        root.classList.toggle("light", theme === "light");
        root.style.colorScheme = theme;
        var meta = document.querySelector('meta[name="theme-color"]');
        if (meta) {
            var c = meta.getAttribute("data-" + theme);
            if (c) meta.setAttribute("content", c);
        }
    }
    function changed(theme) {
        try { document.dispatchEvent(new CustomEvent("ss-theme", { detail: { theme: theme } })); } catch (e) {}
    }

    apply(effective());

    if (mq) {
        var onSystem = function () {
            if (saved()) return;
            var t = system();
            apply(t);
            changed(t);
        };
        if (mq.addEventListener) mq.addEventListener("change", onSystem);
        else if (mq.addListener) mq.addListener(onSystem);
    }

    function toggle() {
        var next = effective() === "light" ? "dark" : "light";
        // Same as the system theme: forget the choice so the site follows the system again.
        save(next === system() ? null : next);
        apply(next);
        changed(next);
    }

    window.ssTheme = { get: effective, toggle: toggle };

    function bind() {
        apply(effective()); // the theme-color <meta> may come after this script in <head>
        var els = document.querySelectorAll("[data-theme-toggle]");
        for (var i = 0; i < els.length; i++) {
            els[i].addEventListener("click", function (e) { e.preventDefault(); toggle(); });
        }
    }
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", bind);
    else bind();
})();
