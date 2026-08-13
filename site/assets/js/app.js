/* =========================================================
   目次ページの検索・絞り込み

   絞り込みは2つの軸があります。
   ・分野（食事／運動／…）… どれか1つ
   ・メンバー限定 … 入／切
   この2つは組み合わせて使えます。
   ========================================================= */
(function () {
  "use strict";

  function initFilter() {
    var q = document.getElementById("q");
    var chips = Array.prototype.slice.call(document.querySelectorAll(".chip:not(.chip--paid)"));
    var paidChip = document.querySelector(".chip--paid");
    var cards = Array.prototype.slice.call(document.querySelectorAll(".card"));
    var groups = Array.prototype.slice.call(document.querySelectorAll(".grp"));
    var empty = document.getElementById("empty");
    if (!cards.length) return;

    var cat = "all";
    var paidOnly = false;

    function norm(s) {
      return s.toLowerCase().replace(/[ぁ-ん]/g, function (c) {
        return String.fromCharCode(c.charCodeAt(0) + 0x60); // ひらがな→カタカナ
      });
    }

    function apply() {
      var words = norm(q ? q.value.trim() : "").split(/[\s、,　]+/).filter(Boolean);
      var hit = 0;

      cards.forEach(function (card) {
        var okCat = cat === "all" || card.dataset.cat === cat;
        var okPaid = !paidOnly || card.dataset.paid === "1";
        var hay = norm(card.dataset.q || "");
        var okQ = words.every(function (w) { return hay.indexOf(w) !== -1; });
        var show = okCat && okPaid && okQ;
        card.hidden = !show;
        if (show) hit++;
      });

      groups.forEach(function (g) {
        g.hidden = !g.querySelector(".card:not([hidden])");
      });
      if (empty) empty.hidden = hit !== 0;
    }

    // 分野：どれか1つを選ぶ
    chips.forEach(function (c) {
      c.addEventListener("click", function () {
        chips.forEach(function (x) { x.classList.remove("is-on"); });
        c.classList.add("is-on");
        cat = c.dataset.f;
        apply();
      });
    });

    // メンバー限定：入／切を切り替える（分野の選択は残る）
    if (paidChip) {
      paidChip.addEventListener("click", function () {
        paidOnly = !paidOnly;
        paidChip.classList.toggle("is-on", paidOnly);
        paidChip.setAttribute("aria-pressed", paidOnly ? "true" : "false");
        apply();
      });
    }

    if (q) q.addEventListener("input", apply);
  }

  document.addEventListener("DOMContentLoaded", initFilter);
})();
