#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""記事のトップ画（見出し画像）を作る。

build.py から呼ばれます。単体で `python3 covers.py` を実行すると
site/img/ に作り直すだけの動きをします。

・写真は使いません。分野ごとの図柄を、記事ごとに少しずつ変えて描きます
・記事名（slug）から形を決めるので、同じ記事なら毎回まったく同じ絵になります
・SVGなので、拡大しても粗くならず、1枚2KB程度です

図柄を変えたいときは、下の CATEGORY_ART の各関数を直してください。
色を変えたいときは PALETTE です。
"""
import hashlib
import io
import os
import random

W, H = 1200, 600  # 横2：縦1。カードでも記事の頭でも同じ形で使います

# 分野ごとの色。members.css の tag--◯◯ と揃えてあります
PALETTE = {
    "food":     "#C6A667",  # 金
    "training": "#BE6E58",  # 赤茶
    "posture":  "#4E7A72",  # 深緑
    "sleep":    "#78879F",  # 青灰
    "mind":     "#7A6896",  # 紫
    "golf":     "#608456",  # 緑
}
NAVY_DEEP = "#0D1430"
GOLD = "#C6A667"


def rng_for(slug):
    """記事名から、毎回同じ結果になる乱数を作る。"""
    seed = int.from_bytes(hashlib.sha256(slug.encode("utf-8")).digest()[:8], "big")
    return random.Random(seed)


def mix(hex_a, hex_b, t):
    """2色を混ぜる。t=0 で a、t=1 で b。"""
    a = [int(hex_a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(hex_b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02X%02X%02X" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ---------------------------------------------------------
# 分野ごとの図柄
#   どの関数も (r, c) を受け取って、SVGの中身の文字列を返します
#   r … 乱数  /  c … その分野の色
# ---------------------------------------------------------
def art_food(r, c):
    """食事：皿と器を思わせる、重なった円。"""
    cx, cy = r.uniform(760, 900), r.uniform(250, 340)
    rad = r.uniform(150, 190)
    o = []
    o.append("<circle cx='%.0f' cy='%.0f' r='%.0f' fill='%s' opacity='.10'/>" % (cx, cy, rad * .66, c))
    o.append("<circle cx='%.0f' cy='%.0f' r='%.0f' fill='none' stroke='%s' stroke-width='2' opacity='.55'/>"
             % (cx, cy, rad, c))
    o.append("<circle cx='%.0f' cy='%.0f' r='%.0f' fill='none' stroke='%s' stroke-width='1.2' opacity='.22'/>"
             % (cx, cy, rad * 1.42, c))
    # 半分だけの弧を、少しずらして重ねる
    for i in range(2):
        rr = rad * (1.75 + i * .38)
        a = r.uniform(-40, 40) + i * 25
        o.append("<path d='M %.0f %.0f A %.0f %.0f 0 0 1 %.0f %.0f' fill='none' stroke='%s' "
                 "stroke-width='1' opacity='.16' transform='rotate(%.0f %.0f %.0f)'/>"
                 % (cx - rr, cy, rr, rr, cx + rr, cy, c, a, cx, cy))
    for i in range(3):
        o.append("<circle cx='%.0f' cy='%.0f' r='%.0f' fill='%s' opacity='.35'/>"
                 % (r.uniform(180, 480), r.uniform(180, 430), r.uniform(3, 7), c))
    return "".join(o)


def art_training(r, c):
    """運動：積み上げた棒。長さを変えて、力の段階を表します。"""
    o = []
    n = r.randint(4, 5)
    top = 300 - (n - 1) * 34
    x0 = r.uniform(560, 640)
    for i in range(n):
        w = r.uniform(180, 470)
        y = top + i * 68
        o.append("<rect x='%.0f' y='%.0f' width='%.0f' height='16' rx='8' fill='%s' opacity='%.2f'/>"
                 % (x0, y, w, c, .28 + i * .13))
    o.append("<line x1='%.0f' y1='%.0f' x2='%.0f' y2='%.0f' stroke='%s' stroke-width='1.4' opacity='.4'/>"
             % (x0 - 34, top - 40, x0 - 34, top + (n - 1) * 68 + 56, c))
    o.append("<circle cx='%.0f' cy='%.0f' r='5' fill='%s' opacity='.7'/>" % (x0 - 34, top - 40, c))
    return "".join(o)


def art_posture(r, c):
    """姿勢・不調：背骨のように積んだ節。ゆるやかに反ります。"""
    o = []
    n = 7
    cx = r.uniform(780, 900)
    bend = r.uniform(26, 46) * r.choice((1, -1))
    for i in range(n):
        t = i / float(n - 1)
        x = cx + bend * (t - .5) * (t - .5) * 4 - bend * .5
        y = 130 + i * 52
        o.append("<rect x='%.0f' y='%.0f' width='104' height='34' rx='17' fill='%s' opacity='%.2f'/>"
                 % (x - 52, y, c, .22 + t * .38))
    o.append("<path d='M %.0f 120 Q %.0f 300 %.0f 500' fill='none' stroke='%s' stroke-width='1.2' "
             "opacity='.3' stroke-dasharray='4 7'/>" % (cx - bend * .5, cx + bend * 1.6, cx - bend * .5, c))
    return "".join(o)


def art_sleep(r, c):
    """睡眠：月と、静かな水平線。"""
    cx, cy = r.uniform(790, 900), r.uniform(230, 300)
    rad = r.uniform(120, 155)
    dx = r.uniform(52, 78)
    o = ["<mask id='m'><rect width='%d' height='%d' fill='black'/>"
         "<circle cx='%.0f' cy='%.0f' r='%.0f' fill='white'/>"
         "<circle cx='%.0f' cy='%.0f' r='%.0f' fill='black'/></mask>"
         % (W, H, cx, cy, rad, cx + dx, cy - dx * .5, rad)]
    o.append("<rect width='%d' height='%d' fill='%s' opacity='.5' mask='url(#m)'/>" % (W, H, c))
    o.append("<circle cx='%.0f' cy='%.0f' r='%.0f' fill='none' stroke='%s' stroke-width='1' opacity='.2'/>"
             % (cx, cy, rad * 1.45, c))
    for i in range(3):
        y = 400 + i * 40
        o.append("<line x1='%.0f' y1='%.0f' x2='%.0f' y2='%.0f' stroke='%s' stroke-width='1.4' "
                 "opacity='%.2f' stroke-linecap='round'/>"
                 % (r.uniform(560, 660), y, r.uniform(900, 1060), y, c, .3 - i * .07))
    for i in range(4):
        o.append("<circle cx='%.0f' cy='%.0f' r='2.5' fill='%s' opacity='.45'/>"
                 % (r.uniform(200, 520), r.uniform(150, 400), c))
    return "".join(o)


def art_mind(r, c):
    """マインド：一点から広がる線。続けることの積み重ねです。"""
    cx, cy = r.uniform(820, 920), r.uniform(280, 340)
    o = []
    n = 13
    base = r.uniform(-52, -20)
    for i in range(n):
        a = base + i * (r.uniform(4.4, 6.2))
        ln = r.uniform(230, 400)
        o.append("<line x1='%.0f' y1='%.0f' x2='%.0f' y2='%.0f' stroke='%s' stroke-width='1.3' "
                 "opacity='%.2f' transform='rotate(%.1f %.0f %.0f)'/>"
                 % (cx, cy, cx - ln, cy, c, .16 + (i % 4) * .1, a, cx, cy))
    o.append("<circle cx='%.0f' cy='%.0f' r='9' fill='%s' opacity='.8'/>" % (cx, cy, c))
    o.append("<circle cx='%.0f' cy='%.0f' r='%.0f' fill='none' stroke='%s' stroke-width='1.2' opacity='.28'/>"
             % (cx, cy, r.uniform(180, 230), c))
    return "".join(o)


def art_golf(r, c):
    """ゴルフ：振り抜いたあとの、球の弧。"""
    x0, y0 = r.uniform(520, 600), 470
    apex = r.uniform(120, 175)
    x1 = r.uniform(1020, 1120)
    o = ["<path d='M %.0f %.0f Q %.0f %.0f %.0f %.0f' fill='none' stroke='%s' stroke-width='2' "
         "opacity='.5'/>" % (x0, y0, (x0 + x1) / 2, apex, x1, y0 - 40, c)]
    o.append("<path d='M %.0f %.0f Q %.0f %.0f %.0f %.0f' fill='none' stroke='%s' stroke-width='1' "
             "opacity='.22' stroke-dasharray='3 8'/>"
             % (x0, y0, (x0 + x1) / 2, apex + 70, x1, y0 - 40, c))
    o.append("<circle cx='%.0f' cy='%.0f' r='10' fill='%s' opacity='.85'/>" % (x0, y0, c))
    o.append("<circle cx='%.0f' cy='%.0f' r='5' fill='%s' opacity='.5'/>" % (x1, y0 - 40, c))
    o.append("<line x1='%.0f' y1='%.0f' x2='%d' y2='%.0f' stroke='%s' stroke-width='1.2' opacity='.3'/>"
             % (x0 - 260, y0 + 26, W - 60, y0 + 26, c))
    return "".join(o)


CATEGORY_ART = {
    "food": art_food,
    "training": art_training,
    "posture": art_posture,
    "sleep": art_sleep,
    "mind": art_mind,
    "golf": art_golf,
}


# ---------------------------------------------------------
# 1枚を組み立てる
# ---------------------------------------------------------
def cover_svg(slug, cat, paid=False):
    r = rng_for(slug)
    c = PALETTE.get(cat, GOLD)
    art = CATEGORY_ART.get(cat, art_food)

    # 背景。紺を土台に、その分野の色をほんの少し混ぜます
    bg_a = mix(NAVY_DEEP, c, .06)
    bg_b = mix(NAVY_DEEP, c, .22)
    gx, gy = r.uniform(58, 88), r.uniform(20, 55)
    tilt = r.choice((18, -18, 24, -24))

    return (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 %d %d' width='%d' height='%d' "
        "role='img' aria-hidden='true'>" % (W, H, W, H) +
        "<defs>"
        "<linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>"
        "<stop offset='0' stop-color='%s'/><stop offset='1' stop-color='%s'/></linearGradient>" % (bg_a, bg_b) +
        "<radialGradient id='w' cx='%.0f%%' cy='%.0f%%' r='62%%'>"
        "<stop offset='0' stop-color='%s' stop-opacity='.34'/>"
        "<stop offset='1' stop-color='%s' stop-opacity='0'/></radialGradient>" % (gx, gy, c, c) +
        "<pattern id='p' width='26' height='26' patternUnits='userSpaceOnUse' "
        "patternTransform='rotate(%d)'>"
        "<line x1='0' y1='0' x2='0' y2='26' stroke='#FFFFFF' stroke-width='.9' opacity='.045'/>"
        "</pattern>" % tilt +
        "</defs>"
        "<rect width='%d' height='%d' fill='url(#g)'/>" % (W, H) +
        "<rect width='%d' height='%d' fill='url(#p)'/>" % (W, H) +
        "<rect width='%d' height='%d' fill='url(#w)'/>" % (W, H) +
        art(r, c) +
        # 左下の金の線。全記事に共通で入る、ブランドの印です
        "<line x1='60' y1='%d' x2='150' y2='%d' stroke='%s' stroke-width='3' stroke-linecap='round'/>"
        % (H - 58, H - 58, GOLD) +
        # メンバー限定の記事だけ、金の枠を足します
        ("<rect x='16' y='16' width='%d' height='%d' fill='none' stroke='%s' stroke-width='1.5' "
         "opacity='.5' rx='4'/>" % (W - 32, H - 32, GOLD) if paid else "") +
        "</svg>"
    )


def write_covers(docs, out_dir):
    """自動生成の図柄を書き出す。写真を置いた記事（cover が .svg 以外）は飛ばす。"""
    os.makedirs(out_dir, exist_ok=True)
    n = 0
    for d in docs:
        if not d.get("cover", "").endswith(".svg"):
            continue
        io.open(os.path.join(out_dir, d["slug"] + ".svg"), "w", encoding="utf-8").write(
            cover_svg(d["slug"], d["cat"], d.get("paid", False)))
        n += 1
    return n


if __name__ == "__main__":
    import build
    build.main()
