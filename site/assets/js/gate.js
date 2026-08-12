/* =========================================================
   会員ページ — 合言葉ゲート ＋ 検索・絞り込み
   合言葉そのものは埋め込まず、ハッシュだけを持ちます。
   ========================================================= */
(function () {
  "use strict";

  var HASH = "d1d6171f67d38e77199d5e5a304fd351ce81199bd16a09d0b658cc0ca400964e";
  var KEY = "dlight-members";

  // ---------- 合言葉 ----------
  // 大文字・小文字と前後の空白は無視して照合する
  function sha256(text) {
    var buf = new TextEncoder().encode(String(text).trim().toLowerCase());
    return crypto.subtle.digest("SHA-256", buf).then(function (d) {
      return Array.prototype.map
        .call(new Uint8Array(d), function (b) { return b.toString(16).padStart(2, "0"); })
        .join("");
    });
  }

  function unlock() {
    document.documentElement.classList.remove("gated");
    var g = document.getElementById("gate");
    if (g) g.remove();
  }

  function showGate() {
    var g = document.getElementById("gate");
    if (!g) return;
    g.hidden = false;
    var form = document.getElementById("gate-form");
    var input = document.getElementById("gate-input");
    var err = document.getElementById("gate-err");
    input.focus();
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      sha256(input.value.trim()).then(function (h) {
        if (h === HASH) {
          try { localStorage.setItem(KEY, h); } catch (_) {}
          unlock();
        } else {
          err.hidden = false;
          input.value = "";
          input.focus();
        }
      });
    });
  }

  function check() {
    // ① 保存済みか
    var saved = null;
    try { saved = localStorage.getItem(KEY); } catch (_) {}
    if (saved === HASH) { unlock(); return; }

    // ② URLの鍵（?k=合言葉）— LINEのリッチメニュー用。入力せずに開けます
    var k = new URLSearchParams(location.search).get("k");
    if (k) {
      sha256(k).then(function (h) {
        if (h === HASH) {
          try { localStorage.setItem(KEY, h); } catch (_) {}
          history.replaceState(null, "", location.pathname);
          unlock();
        } else {
          showGate();
        }
      });
      return;
    }
    showGate();
  }

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
        var okCat = cat === "all" || card.dataset.cat === cat;
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

  document.addEventListener("DOMContentLoaded", function () {
    check();
    initFilter();
  });
})();
