/* =========================================================
   目次ページの検索・絞り込み

   絞り込みは2つの軸があります。
   ・分野（食事／運動／…）… どれか1つ。記事は複数の分野を持てます
   ・メンバー限定 … 入／切
   この2つは組み合わせて使えます。

   検索は、タイトル・結論・キーワードに加えて、本文の中も探します。
   （メンバー限定の記事の本文は入っていません）
   ========================================================= */
(function () {
  "use strict";

  function norm(s) {
    return String(s).toLowerCase().replace(/[ぁ-ん]/g, function (c) {
      return String.fromCharCode(c.charCodeAt(0) + 0x60); // ひらがな→カタカナ
    });
  }

  function initFilter() {
    var q = document.getElementById("q");
    var chips = Array.prototype.slice.call(document.querySelectorAll(".chip:not(.chip--paid)"));
    var paidChip = document.querySelector(".chip--paid");
    var cards = Array.prototype.slice.call(document.querySelectorAll(".card"));
    var heads = Array.prototype.slice.call(document.querySelectorAll(".grp__hd"));
    var empty = document.getElementById("empty");
    var hits = document.getElementById("hits");
    if (!cards.length) return;

    var cat = "all";
    var paidOnly = false;

    // 本文を読み込んで、検索できる形にしておく（1回だけ）
    var body = {};
    var raw = document.getElementById("fulltext");
    if (raw) {
      try {
        var data = JSON.parse(raw.textContent);
        for (var k in data) { body[k] = norm(data[k]); }
      } catch (e) { /* 本文が読めなくても、見出しだけで検索できます */ }
    }

    function apply() {
      var words = norm(q ? q.value.trim() : "").split(/[\s、,　]+/).filter(Boolean);
      var searching = words.length > 0;
      var hit = 0;

      cards.forEach(function (card) {
        var cats = (card.dataset.cats || "").split(" ");
        var okCat = cat === "all" || cats.indexOf(cat) !== -1;
        var okPaid = !paidOnly || card.dataset.paid === "1";
        var hay = norm(card.dataset.q || "");
        var txt = body[card.dataset.slug] || "";
        var okQ = words.every(function (w) {
          return hay.indexOf(w) !== -1 || txt.indexOf(w) !== -1;
        });
        var show = okCat && okPaid && okQ;
        card.hidden = !show;
        if (show) hit++;
      });

      // 分野で絞ったときと検索中は、分野の見出しを消してカードを詰めます
      var plain = cat !== "all" || paidOnly || searching;
      heads.forEach(function (h) { h.hidden = plain; });

      if (empty) empty.hidden = hit !== 0;
      if (hits) {
        hits.hidden = !(searching || plain) || hit === 0;
        hits.textContent = hit + "件";
      }
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
