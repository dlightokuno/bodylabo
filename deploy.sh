#!/bin/bash
# =========================================================
# 【使いません】Netlify に送るための古いスクリプトです
#
# いまの公開先は GitHub Pages です。公開するときは
#
#     python3 publish.py
#
# を実行してください。
#
# Netlify はアカウントのクレジットを使い切っていて、送っても弾かれます。
# 中身は下に残してありますが、実行しても止まるようにしてあります。
# =========================================================
cat <<'MSG'

  このスクリプトは使いません。

  公開先は GitHub Pages に移りました。次を実行してください。

      python3 publish.py

  公開URL: https://dlightokuno.github.io/bodylabo-site/

MSG
exit 1

# ------- 以下、以前の内容（実行されません） -------
# python3 build.py
# netlify deploy --prod --dir site --no-build
