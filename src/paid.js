/* =========================================================
   有料記事の復号
   本文は暗号化された状態でページに埋め込まれています。
   合言葉から鍵を作り、その鍵でしか読めません。
   ソースを見ても、合言葉を知らなければ本文は取り出せません。
   ========================================================= */
(function () {
  "use strict";

  var KEY = "dlight-members-paid";
  var box = document.getElementById("paid");
  if (!box) return;

  var data = JSON.parse(document.getElementById("paid-data").textContent);

  function b64(s) {
    var bin = atob(s), a = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) a[i] = bin.charCodeAt(i);
    return a;
  }

  // 合言葉 → 鍵（時間のかかる変換なので、総当たりが現実的でなくなります）
  function deriveKey(pass) {
    var enc = new TextEncoder();
    return crypto.subtle
      .importKey("raw", enc.encode(String(pass).trim().toLowerCase()), "PBKDF2", false, ["deriveBits"])
      .then(function (k) {
        return crypto.subtle.deriveBits(
          { name: "PBKDF2", salt: b64(data.salt), iterations: data.iter, hash: "SHA-256" },
          k, 256);
      })
      .then(function (bits) { return new Uint8Array(bits); });
  }

  function sha256(bytes) {
    return crypto.subtle.digest("SHA-256", bytes).then(function (d) { return new Uint8Array(d); });
  }

  function concat(a, b) {
    var out = new Uint8Array(a.length + b.length);
    out.set(a, 0); out.set(b, a.length);
    return out;
  }

  // 鍵が合っているかを、本文を復号する前に確かめる
  function checkKey(key) {
    return sha256(concat(key, new TextEncoder().encode("check"))).then(function (h) {
      var hex = Array.prototype.map.call(h.subarray(0, 8),
        function (b) { return b.toString(16).padStart(2, "0"); }).join("");
      return hex === data.check;
    });
  }

  // 鍵から本文と同じ長さの列を作り、重ね合わせて元に戻す
  function decrypt(key) {
    var ct = b64(data.body);
    var blocks = Math.ceil(ct.length / 32);
    var jobs = [];
    for (var i = 0; i < blocks; i++) {
      var c = new Uint8Array(4);
      new DataView(c.buffer).setUint32(0, i, false);
      jobs.push(sha256(concat(key, c)));
    }
    return Promise.all(jobs).then(function (stream) {
      var out = new Uint8Array(ct.length);
      for (var i = 0; i < ct.length; i++) out[i] = ct[i] ^ stream[i >> 5][i & 31];
      return new TextDecoder().decode(out);
    });
  }

  function open(html) {
    box.outerHTML = html;
    document.querySelectorAll(".art__body .sec").forEach(function (el, i) {
      el.style.animation = "fadein .4s " + (i * 0.05) + "s var(--ease) both";
    });
  }

  function unlock(pass, remember) {
    return deriveKey(pass).then(function (key) {
      return checkKey(key).then(function (ok) {
        if (!ok) return false;
        if (remember) { try { localStorage.setItem(KEY, pass); } catch (_) {} }
        return decrypt(key).then(function (html) { open(html); return true; });
      });
    });
  }

  // 保存済みの合言葉があれば、聞かずに開く
  var saved = null;
  try { saved = localStorage.getItem(KEY); } catch (_) {}
  if (saved) unlock(saved, false);

  var form = document.getElementById("paid-form");
  var input = document.getElementById("paid-input");
  var err = document.getElementById("paid-err");
  var btn = form.querySelector("button");

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    err.hidden = true;
    btn.disabled = true;
    btn.textContent = "確認中…";
    unlock(input.value, true).then(function (ok) {
      if (!ok) {
        err.hidden = false;
        input.value = "";
        input.focus();
        btn.disabled = false;
        btn.textContent = "読む";
      }
    });
  });
})();
