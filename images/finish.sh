#!/bin/bash
# 生成した画像（images/_raw/*.png）を、サイト用の軽いJPEGに変換します。
#
#   bash images/finish.sh
#
# ・横1200pxに縮めます（トップ画としてはこれで十分です）
# ・PNG 約1.5MB → JPEG 約150KB。49枚で 70MB が 7MB になります
# ・build.py は images/<slug>.jpg を見つけると、自動生成の図柄より優先して使います
set -euo pipefail
cd "$(dirname "$0")"

n=0
for src in _raw/*.png; do
  [ -e "$src" ] || continue
  slug="$(basename "$src" .png)"
  sips -Z 1200 -s format jpeg -s formatOptions 72 "$src" --out "./$slug.jpg" >/dev/null
  n=$((n + 1))
done
echo "■ $n 枚を jpg にしました"
du -sh . 2>/dev/null | awk '{print "  images/ 全体: " $1}'
