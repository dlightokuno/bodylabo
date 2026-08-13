#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""原稿(.md)から会員ページのHTMLを生成する。

使い方:  python3 build.py
出力先:  site/
原本は .md のほうです。HTMLは毎回作り直されるので直接編集しないでください。

無料記事は誰でも読めます。
原稿の frontmatter に `paid: true` を書いた記事だけ、本文が暗号化され、
合言葉を入れないと読めなくなります（結論の一行だけは見出しとして残ります）。
"""
import base64
import glob
import hashlib
import html
import io
import json
import os
import re
import shutil
import struct

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "site")

# =========================================================
# 有料記事の合言葉（変更したらここを書き換えて build.py を再実行）
#
# ・辞書にある単語は使わないでください。ハッシュから割り出されます
# ・大文字小文字と前後の空白は無視して照合します
# =========================================================
PAID_PASSWORD = "labo-9x4k2m"
# 合言葉から鍵を作るときの繰り返し回数。総当たりを重くするためのもの。
# 増やすほど破りにくくなりますが、そのぶん読者の待ち時間が伸びます。
# 合言葉が推測しにくい文字列であれば、この値で十分です。
PAID_ITER = 300000

# ブランド表記（ロゴはここを直せば全ページ変わります）
BRAND_MAIN = "D/LIGHT"        # 前半（スラッシュは自動で金色になります）
BRAND_SUB = "BODY LABO"       # 後半
SITE_NAME = "D/LIGHT BODY LABO"
PAGE_NAME = "会員ページ"

# 公式サイトへのリンクを出す場合はURLを入れる（空なら出しません）
HOME_URL = ""

# 検索エンジンに載せない
NOINDEX = True

# 分野の並び順と表示名（この順でトップに並びます）
CATEGORIES = [
    ("scene", "困った場面", "外食・飲み会・食べすぎ"),
    ("base", "食事の基本", "何を、どれだけ"),
    ("num", "数字と続け方", "体重・記録・停滞期"),
    ("training", "運動・トレーニング", "筋トレ・有酸素"),
    ("posture", "姿勢・不調", "肩こり・姿勢・むくみ"),
    ("sleep", "睡眠・頭痛", "眠り・頭の重さ"),
    ("mind", "続け方・気持ち", "挫折・リバウンド"),
    ("golf", "ゴルフ", "ラウンドと体の使い方"),
]
CATEGORY_OF = {
    "困った場面": "scene",
    "食事の基本": "base",
    "数字と続け方": "num",
    "運動・トレーニング": "training",
    "姿勢・不調": "posture",
    "不調・姿勢": "posture",
    "睡眠・頭痛": "sleep",
    "睡眠": "sleep",
    "睡眠・頭部": "sleep",
    "続け方・気持ち": "mind",
    "ゴルフ": "golf",
    # 旧・分ける前の呼び名
    "ダイエット": "base",
}


# ---------------------------------------------------------
# Markdown の読み取り
# ---------------------------------------------------------
def read_doc(path):
    raw = io.open(path, encoding="utf-8").read()
    meta = {}
    if raw.startswith("---"):
        _, fm, raw = raw.split("---", 2)
        for line in fm.strip().split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                v = v.split("#")[0].strip()
                meta[k.strip()] = None if v in ("null", "") else v

    title = ""
    sections = []  # [(heading, [lines])]
    current = None
    for line in raw.split("\n"):
        if line.startswith("# "):
            title = line[2:].strip()
        elif line.startswith("## "):
            current = (line[3:].strip(), [])
            sections.append(current)
        elif current is not None:
            current[1].append(line)

    meta["title"] = title
    meta["file"] = os.path.basename(path)
    return meta, sections


def inline(text):
    """**強調** だけを変換する。それ以外はエスケープする。"""
    parts = re.split(r"\*\*(.+?)\*\*", text)
    out = []
    for i, p in enumerate(parts):
        out.append("<strong>%s</strong>" % html.escape(p) if i % 2 else html.escape(p))
    return "".join(out)


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def blocks_to_html(lines):
    """通常セクション（承・転）の本文を組む。"""
    out, ul, table = [], [], []

    def flush_ul():
        if ul:
            out.append("<ul class='list'>%s</ul>" % "".join("<li>%s</li>" % x for x in ul))
            ul.clear()

    def flush_table():
        """| で区切った行を表にする。2行目の |---| は区切りなので飛ばす。"""
        if not table:
            return
        rows = [r for r in table if not set(r.replace("|", "").replace(" ", "")) <= set("-:")]
        if rows:
            head = "".join("<th>%s</th>" % inline(c) for c in cells(rows[0]))
            body = "".join(
                "<tr>%s</tr>" % "".join("<td>%s</td>" % inline(c) for c in cells(r))
                for r in rows[1:])
            out.append("<div class='tablewrap'><table><thead><tr>%s</tr></thead>"
                       "<tbody>%s</tbody></table></div>" % (head, body))
        table.clear()

    for line in lines:
        s = line.strip()
        if s.startswith("|"):
            flush_ul()
            table.append(s)
            continue
        flush_table()
        if not s or s == "---":
            flush_ul()
        elif s.startswith("- "):
            ul.append(inline(s[2:]))
        elif s.startswith("> "):
            flush_ul()
            out.append("<p class='note'>%s</p>" % inline(s[2:]))
        else:
            flush_ul()
            out.append("<p>%s</p>" % inline(s))
    flush_ul()
    flush_table()
    return "\n".join(out)


STEP_RE = re.compile(r"^\*\*(\d+)\.\s*(.+?)\*\*$")


def steps_to_html(lines):
    """「やること」を番号付きのカードに組む。末尾の注意書きは外に出す。"""
    steps, notes, cur = [], [], None
    for line in lines:
        s = line.strip()
        if not s or s == "---":
            continue
        m = STEP_RE.match(s)
        if m:
            cur = {"n": m.group(1), "head": inline(m.group(2)), "body": []}
            steps.append(cur)
        elif s.startswith("> "):
            notes.append(inline(s[2:]))
        elif cur is not None:
            cur["body"].append(inline(s))

    cards = "".join(
        "<li class='step'><span class='step__n'>{n}</span>"
        "<div class='step__c'><h3>{head}</h3>{body}</div></li>".format(
            n=s["n"], head=s["head"], body="".join("<p>%s</p>" % b for b in s["body"])
        )
        for s in steps
    )
    html_out = "<ol class='steps'>%s</ol>" % cards
    for n in notes:
        html_out += "<p class='note'>%s</p>" % n
    return html_out


# ---------------------------------------------------------
# 有料記事の暗号化
# ---------------------------------------------------------
def encrypt(text, password):
    """合言葉から鍵を作り、本文を読めない形にする。

    ページに入るのは、この関数が返す値だけです。合言葉そのものは入りません。
    """
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.strip().lower().encode("utf-8"),
                              salt, PAID_ITER, 32)
    # 合言葉が合っているかを、本文を戻す前に確かめるための短い印
    check = hashlib.sha256(key + b"check").hexdigest()[:16]

    data = text.encode("utf-8")
    stream = b"".join(hashlib.sha256(key + struct.pack(">I", i)).digest()
                      for i in range((len(data) + 31) // 32))
    body = bytes(a ^ b for a, b in zip(data, stream))

    return {
        "salt": base64.b64encode(salt).decode(),
        "body": base64.b64encode(body).decode(),
        "check": check,
        "iter": PAID_ITER,
    }


# ---------------------------------------------------------
# テンプレート
# ---------------------------------------------------------
def logo(cls):
    """D/LIGHT BODY LABO のロゴ。スラッシュだけ金色にする。"""
    main = html.escape(BRAND_MAIN).replace("/", "<span>/</span>")
    return "<span class='%s__a'>%s</span><span class='%s__b'>%s</span>" % (
        cls, main, cls, html.escape(BRAND_SUB))


def head(title, desc, paid=False):
    robots = ('<meta name="robots" content="noindex, nofollow, noarchive">\n'
              if NOINDEX else "")
    scripts = '<script src="assets/js/app.js" defer></script>'
    if paid:
        scripts += '\n<script src="assets/js/paid.js" defer></script>'
    return """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{robots}<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="theme-color" content="#16204A">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Jost:wght@300;400;500&family=Noto+Sans+JP:wght@400;500;700&family=Zen+Old+Mincho:wght@400;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/css/members.css">
{scripts}
</head>
<body>
""".format(title=html.escape(title), desc=html.escape(desc), robots=robots, scripts=scripts)


def header():
    home = ('<a class="hd__home" href="%s" target="_blank" rel="noopener">公式サイト</a>'
            % HOME_URL) if HOME_URL else ""
    return """<header class="hd">
  <div class="hd__in">
    <a class="hd__logo" href="index.html">{logo}</a>
    {home}
  </div>
</header>
""".format(home=home, logo=logo("hd__logo"))


FOOTER = """<footer class="ft">
  <p class="ft__logo">{logo}</p>
  <p class="ft__txt">このページは会員の方向けです。内容についてのご質問は、セッションのときに担当トレーナーへどうぞ。</p>
</footer>
</body>
</html>
""".format(logo=logo("ft__logo"))


PAID_FORM = """<div class="paid" id="paid">
  <p class="paid__mark">この先は有料です</p>
  <p class="paid__lead">続きは、お求めいただいた方だけが読めます。<br>
    合言葉を入力してください。一度入れると、この端末では次回から聞かれません。</p>
  <form class="paid__form" id="paid-form">
    <input class="paid__input" id="paid-input" type="password" autocomplete="current-password"
           placeholder="合言葉" aria-label="合言葉">
    <button class="paid__btn" type="submit">読む</button>
  </form>
  <p class="paid__err" id="paid-err" hidden>合言葉が違います。</p>
  <p class="paid__help">お求めになるときは、セッションのときに担当トレーナーへお申し付けください。</p>
</div>"""


def article_page(meta, sections, prev, nxt):
    cat_key = CATEGORY_OF.get(meta.get("category", ""), "diet")
    cat_name = dict((k, n) for k, n, _ in CATEGORIES)[cat_key]
    is_paid = str(meta.get("paid", "")).lower() == "true"

    lead_head = sections[0][0]
    lead_txt = lead_head.split("：", 1)[-1].strip()

    body = ""
    for h, lines in sections[1:]:
        if h.startswith("やること"):
            body += "<section class='sec sec--do'><h2>%s</h2>%s</section>" % (
                html.escape(h), steps_to_html(lines))
        else:
            body += "<section class='sec'><h2>%s</h2>%s</section>" % (
                html.escape(h), blocks_to_html(lines))

    video = ""
    if meta.get("video"):
        video = ("<div class='video'><iframe src='https://www.youtube-nocookie.com/embed/"
                 "{vid}?rel=0&playsinline=1' title='動画' loading='lazy' allowfullscreen "
                 "frameborder='0'></iframe></div>").format(vid=html.escape(meta["video"]))

    if is_paid:
        # 本文は暗号化して埋め込む。合言葉なしでは取り出せません
        enc = encrypt(body, PAID_PASSWORD)
        body = (PAID_FORM +
                '<script type="application/json" id="paid-data">%s</script>'
                % json.dumps(enc, ensure_ascii=True))
        video = ""  # 動画も有料側に置く場合は本文に含めてください

    nav = ""
    if prev or nxt:
        nav = "<nav class='pager'>"
        nav += ("<a class='pager__l' href='%s.html'><span>前の記事</span><b>%s</b></a>"
                % (prev["slug"], html.escape(prev["title"]))) if prev else "<span></span>"
        nav += ("<a class='pager__r' href='%s.html'><span>次の記事</span><b>%s</b></a>"
                % (nxt["slug"], html.escape(nxt["title"]))) if nxt else "<span></span>"
        nav += "</nav>"

    tags = "<span class='tag tag--{cat}'>{catname}</span>".format(
        cat=cat_key, catname=html.escape(cat_name))
    if is_paid:
        tags += "<span class='tag tag--paid'>有料</span>"

    return (head(meta["title"] + "｜" + SITE_NAME + " " + PAGE_NAME, lead_txt, paid=is_paid)
            + header()
            + """<main class="art">
  <div class="art__hd">
    <a class="back" href="index.html">一覧にもどる</a>
    <div class="tags">{tags}</div>
    <h1>{title}</h1>
  </div>
  <div class="lead">
    <p class="lead__label">結論</p>
    <p class="lead__txt">{lead}</p>
  </div>
  {video}
  <div class="art__body">{body}</div>
  {nav}
</main>
""".format(tags=tags, title=html.escape(meta["title"]),
           lead=inline(lead_txt), video=video, body=body, nav=nav)
            + FOOTER)


def index_page(docs):
    chips = "<button class='chip is-on' data-f='all'>すべて</button>"
    for key, name, _ in CATEGORIES:
        if any(d["cat"] == key for d in docs):
            chips += "<button class='chip' data-f='%s'>%s</button>" % (key, html.escape(name))

    groups = ""
    for key, name, sub in CATEGORIES:
        items = [d for d in docs if d["cat"] == key]
        if not items:
            continue
        cards = ""
        for d in items:
            tag = ("<span class='card__tag tag tag--paid'>有料</span>" if d["paid"]
                   else "<span class='card__tag tag tag--%s'>%s</span>" % (d["cat"], html.escape(name)))
            cards += """<li class="card{pc}" data-cat="{cat}" data-q="{q}">
      <a href="{slug}.html">
        {tag}
        <h3 class="card__t">{title}</h3>
        <p class="card__l">{lead}</p>
        <span class="card__go">{go}</span>
      </a>
    </li>""".format(cat=d["cat"], tag=tag, slug=d["slug"], pc=" card--paid" if d["paid"] else "",
                    title=html.escape(d["title"]), lead=html.escape(d["lead"]),
                    go="続きを読む" if d["paid"] else "読む",
                    q=html.escape(d["title"] + " " + d["lead"] + " " + d["kw"]))
        groups += """<section class="grp" data-cat="{cat}">
    <div class="grp__hd"><h2>{name}</h2><p>{sub}</p></div>
    <ul class="cards">{cards}</ul>
  </section>""".format(cat=key, name=html.escape(name), sub=html.escape(sub), cards=cards)

    return (head(SITE_NAME + " " + PAGE_NAME, "会員の方向けの読みものです。")
            + header()
            + """<main class="top">
  <section class="hero">
    <p class="hero__eyebrow">MEMBERS</p>
    <h1 class="hero__t">からだの悩みから、探す。</h1>
    <p class="hero__l">セッションのあいだに全部は話しきれません。<br>
      家での24時間のために、よく聞かれることをまとめました。</p>
  </section>

  <div class="filter">
    <div class="chips">{chips}</div>
    <div class="search">
      <input id="q" type="search" placeholder="キーワードで探す（例：停滞、外食、肩）" aria-label="キーワードで探す">
    </div>
  </div>

  <div id="groups">{groups}</div>
  <p class="empty" id="empty" hidden>該当する記事がありませんでした。</p>
</main>
""".format(chips=chips, groups=groups)
            + FOOTER)


# ---------------------------------------------------------
# 生成
# ---------------------------------------------------------
def main():
    docs = []
    # 記事の原本は「01-」のように数字で始まるファイルだけ。README などは対象外。
    for path in sorted(glob.glob(os.path.join(ROOT, "[0-9][0-9]-*.md"))):
        meta, sections = read_doc(path)
        if not sections or not meta.get("slug"):
            continue
        lead_head = sections[0][0]
        docs.append({
            "slug": meta["slug"],
            "title": meta["title"],
            "lead": lead_head.split("：", 1)[-1].strip(),
            "cat": CATEGORY_OF.get(meta.get("category", ""), "diet"),
            "kw": meta.get("keywords") or "",
            "paid": str(meta.get("paid", "")).lower() == "true",
            "meta": meta,
            "sections": sections,
        })

    order = {k: i for i, (k, _, _) in enumerate(CATEGORIES)}
    docs.sort(key=lambda d: (order.get(d["cat"], 9), d["meta"]["file"]))

    os.makedirs(os.path.join(OUT, "assets", "css"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "assets", "js"), exist_ok=True)

    for i, d in enumerate(docs):
        prev = docs[i - 1] if i > 0 else None
        nxt = docs[i + 1] if i < len(docs) - 1 else None
        io.open(os.path.join(OUT, d["slug"] + ".html"), "w", encoding="utf-8").write(
            article_page(d["meta"], d["sections"], prev, nxt))

    io.open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(index_page(docs))

    # 原稿を消した記事のページが残らないように掃除する
    keep = {d["slug"] + ".html" for d in docs} | {"index.html"}
    for name in os.listdir(OUT):
        if name.endswith(".html") and name not in keep:
            os.remove(os.path.join(OUT, name))
            print("  （削除）%s" % name)
    io.open(os.path.join(OUT, "robots.txt"), "w", encoding="utf-8").write(
        "User-agent: *\nDisallow: /\n" if NOINDEX else "User-agent: *\nAllow: /\n")

    for name in ("app.js", "paid.js"):
        shutil.copy(os.path.join(ROOT, "src", name),
                    os.path.join(OUT, "assets", "js", name))
    shutil.copy(os.path.join(ROOT, "src", "members.css"),
                os.path.join(OUT, "assets", "css", "members.css"))
    # 以前あった合言葉ゲートの名残を消す
    old = os.path.join(OUT, "assets", "js", "gate.js")
    if os.path.exists(old):
        os.remove(old)

    paid = [d for d in docs if d["paid"]]
    print("生成しました: %d記事（うち有料%d）+ 目次" % (len(docs), len(paid)))
    for d in docs:
        print("  %-8s %s%s" % (d["cat"], "[有料] " if d["paid"] else "", d["title"]))


if __name__ == "__main__":
    main()
