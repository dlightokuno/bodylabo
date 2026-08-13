/* =========================================================
   目次ページの検索・絞り込み
   ========================================================= */
(function () {
  "use strict";

  // ---------- 検索・絞り込み ----------
  function initFilter() {
    var q = document.getElementById("q");
    var chips = Array.prototype.slice.call(document.querySelectorAll(".chip"));
    var cards = Array.prototype.slice.call(document.querySelectorAll(".card"));
    var groups = Array.prototype.slice.call(document.querySelectorAll(".grp"));
    var empty = document.getElementById("empty");
    if (!cards.length) return;

    var cat = "all";

    function norm(s) {
      return s.toLowerCase().replace(/[ぁ-ん]/g, function (c) {
        return String.fromCharCode(c.charCodeAt(0) + 0x60); // ひらがな→カタカナ
      });
    }

    function apply() {
      var words = norm(q ? q.value.trim() : "").split(/[\s、,　]+/).filter(Boolean);
      var hit = 0;

      cards.forEach(function (card) {
        // 「有料」は分野ではなく、有料かどうかで絞ります
        var okCat = cat === "all" ||
          (cat === "paid" ? card.dataset.paid === "1" : card.dataset.cat === cat);
        var hay = norm(card.dataset.q || "");
        var okQ = words.every(function (w) { return hay.indexOf(w) !== -1; });
        var show = okCat && okQ;
        card.hidden = !show;
        if (show) hit++;
      });

      groups.forEach(function (g) {
        g.hidden = !g.querySelector(".card:not([hidden])");
      });
      if (empty) empty.hidden = hit !== 0;
    }

    chips.forEach(function (c) {
      c.addEventListener("click", function () {
        chips.forEach(function (x) { x.classList.remove("is-on"); });
        c.classList.add("is-on");
        cat = c.dataset.f;
        apply();
      });
    });
    if (q) q.addEventListener("input", apply);
  }

  document.addEventListener("DOMContentLoaded", initFilter);
})();
