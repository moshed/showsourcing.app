// Help search for showsourcing.app/help. Runs in the browser, no server, no model.
// The app uses the same rules in HelpRanker.swift (plus on-device sentence
// vectors), and scripts/help_eval scores both on the same questions.
//
// Rules: drop stopwords ("can i", "how do i"), light stemming, a synonym map
// (qty -> quantity), and hand-written "asks" (how people phrase each question).
// A rare word counts more than a common one (idf). Not every word must match.
(function (root) {
    var W = { question: 5, asks: 5, keywords: 4, answer: 2, section: 1 };

    function fold(s) { return String(s).toLowerCase().normalize("NFKD").replace(/[̀-ͯ]/g, "").replace(/['’]/g, ""); }
    function stem(w) {
        if (w.length > 4 && /ies$/.test(w)) return w.slice(0, -3) + "y";
        if (w.length > 5 && /ing$/.test(w)) return w.slice(0, -3);
        if (w.length > 4 && /ed$/.test(w)) return w.slice(0, -2);
        if (w.length > 4 && /(ses|xes|ches|shes)$/.test(w)) return w.slice(0, -2);
        if (w.length > 3 && /s$/.test(w) && !/ss$/.test(w)) return w.slice(0, -1);
        return w;
    }
    function words(s) { return fold(s).split(/[^a-z0-9]+/).filter(Boolean); }
    function near(a, b) {
        if (Math.abs(a.length - b.length) > 1) return false;
        var i = 0, j = 0, d = 0;
        while (i < a.length && j < b.length) {
            if (a[i] === b[j]) { i++; j++; continue; }
            if (++d > 1) return false;
            if (a.length > b.length) i++; else if (b.length > a.length) j++; else { i++; j++; }
        }
        return d + (a.length - i) + (b.length - j) <= 1;
    }

    function build(help) {
        var stop = {}; (help.stopwords || []).forEach(function (w) { stop[fold(w)] = 1; });
        var syn = help.synonyms || {};
        var tokset = function (text) { var o = {}; words(text).forEach(function (w) { if (!stop[w]) o[stem(w)] = 1; }); return o; };
        var items = [];
        help.sections.forEach(function (s) {
            s.entries.forEach(function (e) {
                var f = {
                    question: tokset(e.question), asks: tokset((e.asks || []).join(" ")),
                    keywords: tokset((e.keywords || []).join(" ")), answer: tokset(e.answer), section: tokset(s.title)
                };
                var all = {}; Object.keys(f).forEach(function (k) { Object.keys(f[k]).forEach(function (t) { all[t] = 1; }); });
                items.push({ entry: e, section: s, fields: f, all: all, allList: Object.keys(all),
                    squashed: fold(e.question + " " + e.answer + " " + (e.keywords || []).join(" ")).replace(/[^a-z0-9]+/g, "") });
            });
        });
        var df = {};
        items.forEach(function (it) { it.allList.forEach(function (t) { df[t] = (df[t] || 0) + 1; }); });
        var n = items.length;
        function idf(t) { return Math.log(1 + n / (df[t] || 1)); }

        function variants(w) {
            var v = {}; v[stem(w)] = 1;
            (syn[w] || syn[stem(w)] || []).forEach(function (x) { words(x).forEach(function (y) { v[stem(y)] = 1; }); });
            return Object.keys(v);
        }

        function search(q) {
            var raw = words(q);
            var qs = raw.filter(function (w) { return !stop[w]; });
            if (!qs.length) qs = raw;
            if (!qs.length) return [];
            var hits = [];
            items.forEach(function (it) {
                var score = 0, matched = 0;
                qs.forEach(function (w) {
                    var best = 0, extra = 0;
                    variants(w).forEach(function (v, vi) {
                        var syn = vi > 0 ? 0.8 : 1;   // a synonym counts a little less
                        for (var k in W) if (it.fields[k][v]) {
                            var x = W[k] * idf(v) * syn;
                            // The best field counts in full; each other field that
                            // has the word adds a little (breaks ties).
                            if (x > best) { extra += best * 0.15; best = x; } else extra += x * 0.15;
                        }
                    });
                    best += extra;
                    if (!best && w.length >= 4) {
                        var s = stem(w);
                        for (var i = 0; i < it.allList.length; i++) if (near(s, it.allList[i])) { best = 1.5 * idf(it.allList[i]); break; }
                    }
                    if (!best && w.length >= 3 && it.squashed.indexOf(w) >= 0) best = 1;
                    if (best) { matched++; score += best; }
                });
                if (matched) hits.push({ entry: it.entry, section: it.section, score: score * (0.4 + 0.6 * matched / qs.length), coverage: matched / qs.length });
            });
            hits.sort(function (a, b) { return b.score - a.score; });
            // Show what is close to the best, never a long tail of one-word matches.
            if (!hits.length) return hits;
            var top = hits[0].score;
            return hits.filter(function (h, i) { return i < 3 || (h.score >= top * 0.45 && h.coverage >= 0.5); }).slice(0, 12);
        }
        return { search: search, words: function (q) { return words(q).filter(function (w) { return !stop[w]; }); } };
    }

    var api = { build: build, fold: fold, stem: stem };
    if (typeof module !== "undefined" && module.exports) module.exports = api; else root.HelpSearch = api;
})(this);
