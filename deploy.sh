#!/bin/bash
# =========================================================
# サイトを作り直して、Netlify に送る
#
#     ./deploy.sh
#
# Netlify にビルド作業をさせず、出来上がったファイルだけを送ります。
# そのため、無料枠のビルド時間は消費しません。
# =========================================================
set -e
cd "$(dirname "$0")"

echo "■ サイトを作り直します"
python3 build.py

echo ""
echo "■ Netlify に送ります（ビルド時間は消費しません）"

# netlify コマンドが入っていれば、それを使う（起動が速い）
if command -v netlify >/dev/null 2>&1; then
  netlify deploy --prod --dir site --no-build
else
  npx --yes netlify-cli@latest deploy --prod --dir site --no-build
fi

echo ""
echo "完了しました。 https://dlight-body-labo.netlify.app/"
