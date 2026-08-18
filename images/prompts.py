#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""記事ごとのトップ画の「絵の指示」をまとめた表。

python3 images/prompts.py  を実行すると images/prompts.tsv ができます。
それを imagegen スキルの batch.sh に渡すと、画像がまとめて作られます。

絵を変えたい記事は、下の SUBJECT の行を書き換えてください。
書き換えたあと、その記事の画像ファイルを消してから batch.sh を回すと作り直されます。
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# すべての画像に共通する指示。トーンはここで揃えます
LEAD = "a wide 2:1 banner. Editorial photography, natural window light, shot on a 50mm lens."
STYLE = ("Calm and premium mood. Muted palette: deep navy shadows, warm cream, soft gold light. "
         "Shallow depth of field, generous negative space, uncluttered composition. "
         "No text, no letters, no numbers, no logos, no watermark, no visible faces.")

# 記事ごとの主役。1枚に1つだけ置きます
SUBJECT = {
    # ---- 食事 ----
    "teitaiki": "A classic round analog bathroom scale on a pale oak floor beside a window, "
                "shot from a low three-quarter angle in morning light. The circular dial window is "
                "clearly visible, with fine tick marks around its edge and a slim red needle resting on it, "
                "so it reads unmistakably as a weighing scale.",
    "gaishoku": "An empty wooden izakaya table set with small ceramic plates and two glasses, warm evening light from the side.",
    "yoru-tabesugi": "A dim kitchen counter at night, a single glass of water standing beside one empty white plate.",
    "taijukei": "A classic round analog bathroom scale on pale bathroom tiles, seen from directly above, "
                "half in soft shadow. The circular dial with fine tick marks and a slim red needle fills "
                "the centre of the frame, so it reads unmistakably as a weighing scale.",
    "kanshoku": "A small ceramic bowl of almonds and a glass of iced tea on a light wooden table.",
    "protein": "A grilled chicken breast and a halved boiled egg on a plain white plate, clean minimal styling.",
    "shishitsu": "A small glass cruet of olive oil beside a few walnuts on a pale stone counter.",
    "toshitsu": "A bowl of freshly steamed white rice on a wooden tray, faint steam rising.",
    "seni": "A wooden cutting board with broccoli, mushrooms and leafy greens, overhead view.",
    "kakoudo": "A rustic bowl of oats topped with berries on a linen cloth, morning light.",
    "konbini": "A single rice ball on a plain paper wrapper beside an unlabelled bottle of green tea on a clean counter.",
    "jisui": "A cast iron pan on a stove with sliced vegetables, steam rising in a warm home kitchen.",
    "kaimono": "A woven shopping basket filled with fresh vegetables, placed on a pale wooden floor.",
    "hayagui": "A pair of wooden chopsticks resting on a ceramic chopstick rest beside a half-finished bowl of rice.",
    "kaisu": "Three identical empty white plates in a row on a linen tablecloth, overhead view.",
    "choshoku": "A simple breakfast of yogurt, a boiled egg and toast on a table by a sunny window.",
    "osake": "A single tall highball glass with ice on a dark wooden bar counter, warm low light.",
    "ryoko": "An open suitcase with neatly folded clothes and a water bottle on a bedroom floor, morning light.",
    "seiri": "A quiet bedside table with a mug of herbal tea and a folded wool blanket, soft diffused light.",
    "calorie-keisan": "A glass measuring cup and a small bowl of rice on a marble kitchen counter, soft daylight.",
    "teitai-kiriwake": "A magnifying glass resting on a blank open notebook on a dark wooden desk, single window light.",
    "pfc-kondate": "An overhead flat lay of a balanced Japanese meal: grilled fish, a rice bowl and greens on a linen cloth.",

    # ---- 姿勢・不調 ----
    "katakori": "The shoulders and upper back of a person seen from behind in a plain neutral top, standing by a window, soft focus, head out of frame.",
    "shisei": "An empty office chair pulled back from a wooden desk near a window, long side light across the floor.",
    "mukumi": "Bare lower legs and feet resting on a pale wooden floor, seen from above, soft daylight, no face.",

    # ---- 睡眠 ----
    "suimin": "A neatly made bed with white linen in a dim bedroom, early morning light through sheer curtains.",
    "atama": "A dim bedroom at night with a small bedside lamp lit and a glass of water on the table.",

    # ---- 運動 ----
    "kintore-yusen": "A pair of dumbbells resting on a dark gym floor, strong side light, empty space around them.",
    "kinniku-tsukanai": "A single barbell weight plate leaning against a concrete wall in an empty gym.",
    "shu2kai": "An empty flat gym bench with a folded white towel on it, morning light from a high window.",
    "shumoku": "A rack of dumbbells lined up in a row, shallow focus falling off along the row.",
    "kinnikutsu": "A foam roller and a rolled towel on a rubber gym floor, low angle.",
    "juryo": "A loaded barbell resting on the floor of a quiet empty gym, dust in the light.",
    "gotsuku": "Close-up of a woman's hands gripping a dumbbell handle, chalk on the fingers, no face in frame.",
    "hiit": "A rowing machine standing alone in a quiet gym, side light, empty room.",
    "form": "A single kettlebell on a rubber gym floor, low angle, clean empty background.",
    "yusanso": "A treadmill facing a large window in a quiet gym, early morning light.",

    # ---- マインド ----
    "kiroku": "An open blank notebook and a pen on a wooden desk, morning light from the left.",
    "kiroku-yameru": "A closed notebook with a pen resting on top of it, dusty afternoon light across the desk.",
    "kigen": "A small hourglass on a bare wooden desk, long shadow, quiet room.",
    "ijiki": "A completely still lake surface at dawn, minimal horizon, soft mist.",
    "hachijitten": "A stack of smooth balanced river stones on a wooden surface, calm neutral background.",
    "rebound": "A single green sprout emerging from dark soil in a small clay pot, morning light.",
    "sengen": "Two coffee cups placed across from each other on a wooden cafe table, warm light, no people.",
    "motivation": "A pair of running shoes placed neatly by a front door, morning light falling across the floor.",
    "saki-ni-yaru": "A crisp linen shirt on a wooden hanger by a window, soft daylight.",
    "kuraberu": "A plain round mirror on a wall reflecting soft window light in a calm empty room.",

    # ---- ゴルフ ----
    "golf-shokuji": "A golf course fairway at sunrise, dew on the grass, long shadows, wide open view.",
    "golf-kaisen": "A white golf ball on a tee on a green fairway, very low angle, morning light behind it.",

    # ---- 姿勢・不調（追加） ----
    "shisei-ishiki": "A laptop raised on a wooden stand with a separate keyboard on a desk by a window, morning light.",
    "desk-suwarikata": "A simple office chair pulled up to a bare wooden desk near a window, long side light on the floor.",
    "sumaho-kubi": "A smartphone held up at eye level against a bright window, only the hands in frame, backlit.",
    "makikata": "The upper back and open arms of a person in a plain neutral top seen from behind by a window, head out of frame.",
    "kotsuban": "A plain wooden stool standing alone in an empty room, strong side light and a long shadow.",
    "kokansetsu": "A person sitting cross-legged on a pale wooden floor, only the lower body in frame, soft daylight.",
    "zenkutsu": "A yoga mat unrolled on a pale wooden floor beside a window, morning light, nothing else in the room.",
    "ashikubi": "Bare feet and lower legs in a deep squat on a wooden floor, seen from the side, heels flat, soft light.",
    "kenkokotsu": "A coiled resistance band resting on a dark rubber gym floor, low angle, side light.",
    "kokyu": "Sheer white curtains lifting in a breeze at an open window, bright soft daylight, empty room.",
    "knee-in": "A pair of training shoes on a rubber gym floor seen straight from the front, very low angle.",
    "ashiura": "Bare feet standing on a pale wooden floor seen from the front, toes spread, soft morning light.",
    "hie": "Two hands wrapped around a warm ceramic mug, close-up, steam rising, no face in frame.",
    "tachishigoto": "A pair of plain flat shoes on a wooden floor beside a tall standing counter, warm afternoon light.",
    "onaka-mie": "A soft cloth tape measure loosely coiled on a pale wooden surface, single window light.",

    # ---- 睡眠（追加） ----
    "yonaka": "A dark bedroom at night with faint moonlight through a gap in the curtain, rumpled white sheets.",
    "nidone": "Strong late-morning sunlight falling across a crumpled white duvet on an empty bed.",
    "nemae-sumaho": "A smartphone lying face down on a wooden bedside table in a dark bedroom, screen off.",
    "caffeine": "An empty espresso cup on a saucer on a pale stone counter, long late-afternoon shadow.",
    "nezake": "A wine glass and a tall glass of water standing side by side on a dark wooden table, dim evening light.",
    "suimin-jikan": "A neatly made bed in a calm empty bedroom, wide view, soft even daylight.",
    "nedame": "A duvet thrown back across an empty bed with harsh midday light cutting over it.",
    "hirune": "An armchair beside a window with a folded wool blanket over the arm, quiet early-afternoon light.",
    "shinshitsu": "A dark bedroom with a narrow gap of cool blue light between heavy curtains.",
    "nemae-shokuji": "A dim kitchen at night, one covered plate left on the counter, single warm light overhead.",
    "asahi": "Curtains drawn open onto bright morning light in a bedroom, light flooding across the floor.",
    "undo-timing": "An empty gym at dusk, dumbbells on the floor, warm low light through a large window.",
    "suiminbusoku-shokuyoku": "A small bowl of chocolate pieces on a dim kitchen counter late at night, single overhead light.",
    "ibiki": "A single pillow with a head-shaped indentation on a made bed, dim early-morning light.",
    "nemurenai-yoru": "One armchair and a small lit floor lamp in an otherwise dark living room at night.",
}


def prompt_for(slug):
    return "%s %s %s" % (LEAD, SUBJECT[slug], STYLE)


def main():
    out = os.path.join(HERE, "prompts.tsv")
    raw = os.path.join(HERE, "_raw")
    with io.open(out, "w", encoding="utf-8") as f:
        for slug in SUBJECT:
            f.write("%s\t%s\n" % (os.path.join(raw, slug + ".png"), prompt_for(slug)))
    print("%s に %d 枚ぶん書きました" % (out, len(SUBJECT)))


if __name__ == "__main__":
    main()
