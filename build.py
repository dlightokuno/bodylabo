#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""原稿(.md)から会員ページのHTMLを生成する。

使い方:  python3 build.py
出力先:  site/
原本は .md のほうです。HTMLは毎回作り直されるので直接編集しないでください。
"""
import glob
import hashlib
import html
import io
import os
import re
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "site")

# =========================================================
# 合言葉（変更したらこのファイルを書き換えて build.py を再実行）
# ページ側にはハッシュだけが埋め込まれます。
# =========================================================
PASSWORD = "karada"

# ブランド表記（ロゴはここを直せば全ページ変わります）
BRAND_MAIN = "D/LIGHT"        # 前半（スラッシュは自動で金色になります）
BRAND_SUB = "BODY LABO"       # 後半
SITE_NAME = "D/LIGHT BODY LABO"
PAGE_NAME = "会員ページ"

# 公式サイトへのリンクを出す場合はURLを入れる（空なら出しません）
HOME_URL = ""

# 分野の並び順と表示名（この順でトップに並びます）
CATEGORIES = [
    ("diet", "ダイエット", "食事・体重・停滞期"),
    ("posture", "姿勢・不調", "肩こり・姿勢"),
    ("sleep", "睡眠・頭痛", "眠り・頭の重さ"),
]
CATEGORY_OF = {
    "ダイエット": "diet",
    "不調・姿勢": "posture",
    "姿勢・不調": "posture",
    "睡眠": "sleep",
    "睡眠・頭部": "sleep",
    "睡眠・頭痛": "sleep",
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


def blocks_to_html(lines):
    """通常セクション（承・転）の本文を組む。"""
    out, ul = [], []

    def flush_ul():
        if ul:
            out.append("<ul class='list'>%s</ul>" % "".join("<li>%s</li>" % x for x in ul))
            ul.clear()

    for line in lines:
        s = line.strip()
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
# テンプレート
# ---------------------------------------------------------
def logo(cls):
    """D/LIGHT BODY LABO のロゴ。スラッシュだけ金色にする。"""
    main = html.escape(BRAND_MAIN).replace("/", "<span>/</span>")
    return "<span class='%s__a'>%s</span><span class='%s__b'>%s</span>" % (
        cls, main, cls, html.escape(BRAND_SUB))


def head(title, desc, depth=0):
    up = "../" * depth
    return """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow, noarchive">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="theme-color" content="#16204A">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Jost:wght@300;400;500&family=Noto+Sans+JP:wght@400;500;700&family=Zen+Old+Mincho:wght@400;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{up}assets/css/members.css">
<script>document.documentElement.classList.add("gated");</script>
<script src="{up}assets/js/gate.js" defer></script>
</head>
<body>
<div id="gate" class="gate" hidden>
  <form class="gate__card" id="gate-form">
    <p class="gate__logo">{logo}</p>
    <h1 class="gate__title">{pagename}</h1>
    <p class="gate__lead">合言葉を入力してください。<br>一度入れると、この端末では次回から聞かれません。</p>
    <input class="gate__input" id="gate-input" type="password" inputmode="text"
           autocomplete="current-password" placeholder="合言葉" aria-label="合言葉">
    <button class="gate__btn" type="submit">開く</button>
    <p class="gate__err" id="gate-err" hidden>合言葉が違います。</p>
    <p class="gate__help">分からないときは、担当トレーナーにお尋ねください。</p>
  </form>
</div>
""".format(title=html.escape(title), desc=html.escape(desc), up=up,
           logo=logo("gate__logo"), pagename=html.escape(PAGE_NAME))


def header(depth=0):
    up = "../" * depth
    home = ('<a class="hd__home" href="%s" target="_blank" rel="noopener">公式サイト</a>'
            % HOME_URL) if HOME_URL else ""
    return """<header class="hd">
  <div class="hd__in">
    <a class="hd__logo" href="{up}index.html">{logo}</a>
    {home}
  </div>
</header>
""".format(up=up, home=home, logo=logo("hd__logo"))


FOOTER = """<footer class="ft">
  <p class="ft__logo">{logo}</p>
  <p class="ft__txt">このページは会員の方向けです。内容についてのご質問は、セッションのときに担当トレーナーへどうぞ。</p>
</footer>
</body>
</html>
""".format(logo=logo("ft__logo"))


def article_page(meta, sections, prev, nxt):
    cat_key = CATEGORY_OF.get(meta.get("category", ""), "diet")
    cat_name = dict((k, n) for k, n, _ in CATEGORIES)[cat_key]

    lead_head, lead_lines = sections[0]
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

    nav = ""
    if prev or nxt:
        nav = "<nav class='pager'>"
        nav += ("<a class='pager__l' href='%s.html'><span>前の記事</span><b>%s</b></a>"
                % (prev["slug"], html.escape(prev["title"]))) if prev else "<span></span>"
        nav += ("<a class='pager__r' href='%s.html'><span>次の記事</span><b>%s</b></a>"
                % (nxt["slug"], html.escape(nxt["title"]))) if nxt else "<span></span>"
        nav += "</nav>"

    return (head(meta["title"] + "｜" + SITE_NAME + " " + PAGE_NAME, lead_txt)
            + header()
            + """<main class="art">
  <div class="art__hd">
    <a class="back" href="index.html">一覧にもどる</a>
    <span class="tag tag--{cat}">{catname}</span>
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
""".format(cat=cat_key, catname=html.escape(cat_name), title=html.escape(meta["title"]),
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
            cards += """<li class="card" data-cat="{cat}" data-q="{q}">
      <a href="{slug}.html">
        <span class="card__tag tag tag--{cat}">{catname}</span>
        <h3 class="card__t">{title}</h3>
        <p class="card__l">{lead}</p>
        <span class="card__go">読む</span>
      </a>
    </li>""".format(cat=d["cat"], catname=html.escape(name), slug=d["slug"],
                    title=html.escape(d["title"]), lead=html.escape(d["lead"]),
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
    for path in sorted(glob.glob(os.path.join(ROOT, "*.md"))):
        meta, sections = read_doc(path)
        if not sections:
            continue
        lead_head = sections[0][0]
        docs.append({
            "slug": meta.get("slug") or os.path.basename(path).split("-")[0],
            "title": meta["title"],
            "lead": lead_head.split("：", 1)[-1].strip(),
            "cat": CATEGORY_OF.get(meta.get("category", ""), "diet"),
            "kw": meta.get("keywords") or "",
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
    io.open(os.path.join(OUT, "robots.txt"), "w", encoding="utf-8").write(
        "User-agent: *\nDisallow: /\n")

    # 合言葉のハッシュを差し込む
    js = io.open(os.path.join(ROOT, "src", "gate.js"), encoding="utf-8").read()
    js = js.replace("__HASH__", hashlib.sha256(PASSWORD.encode("utf-8")).hexdigest())
    io.open(os.path.join(OUT, "assets", "js", "gate.js"), "w", encoding="utf-8").write(js)
    shutil.copy(os.path.join(ROOT, "src", "members.css"),
                os.path.join(OUT, "assets", "css", "members.css"))

    print("生成しました: %d記事 + 目次" % len(docs))
    for d in docs:
        print("  %-10s %s" % (d["cat"], d["title"]))


if __name__ == "__main__":
    main()
