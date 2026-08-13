#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""site/ の中身だけを、公開用リポジトリへ送る。

    python3 publish.py

やっていること:
  1. build.py を実行して site/ を作り直す
  2. site/ の中身を _public/ に写す（原稿の .md は一切入りません）
  3. _public/ をコミットして push する

公開用リポジトリは Public です。原稿を入れないのはそのためです。
有料記事は暗号化された状態でしか出ていきません。
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(ROOT, "site")
PUB = os.path.join(ROOT, "_public")

# 公開用リポジトリ（Public）
REMOTE = "git@github.com:dlightokuno/bodylabo-site.git"


def run(cmd, cwd=None, check=True):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and r.returncode != 0:
        print("失敗:", " ".join(cmd))
        print(r.stderr.strip() or r.stdout.strip())
        sys.exit(1)
    return r


def main():
    # 1. 作り直す
    print("■ サイトを作り直します")
    r = run([sys.executable, os.path.join(ROOT, "build.py")])
    print(r.stdout.strip().split("\n")[0])

    # 2. 公開用フォルダを用意する
    if not os.path.isdir(os.path.join(PUB, ".git")):
        print("■ 公開用リポジトリを取り込みます")
        if os.path.isdir(PUB):
            shutil.rmtree(PUB)
        r = run(["git", "clone", REMOTE, PUB], check=False)
        if r.returncode != 0:
            print("公開用リポジトリを取り込めませんでした。")
            print("GitHub で Public のリポジトリ bodylabo-site を作ってから、もう一度実行してください。")
            print(r.stderr.strip())
            sys.exit(1)

    # 3. 中身を入れ替える（.git は残す）
    print("■ ファイルを写します")
    for name in os.listdir(PUB):
        if name == ".git":
            continue
        path = os.path.join(PUB, name)
        shutil.rmtree(path) if os.path.isdir(path) else os.remove(path)

    for name in os.listdir(SITE):
        src, dst = os.path.join(SITE, name), os.path.join(PUB, name)
        shutil.copytree(src, dst) if os.path.isdir(src) else shutil.copy(src, dst)

    # GitHub Pages に、余計な変換をさせない印
    open(os.path.join(PUB, ".nojekyll"), "w").close()

    # 4. 送る
    r = run(["git", "status", "--porcelain"], cwd=PUB)
    if not r.stdout.strip():
        print("■ 変更はありませんでした")
        return

    files = len([l for l in r.stdout.strip().split("\n")])
    run(["git", "add", "-A"], cwd=PUB)
    run(["git", "commit", "-m", "サイトを更新"], cwd=PUB)
    print("■ 送ります（%d件の変更）" % files)
    run(["git", "push", "origin", "HEAD"], cwd=PUB)
    print("完了しました。")


if __name__ == "__main__":
    main()
