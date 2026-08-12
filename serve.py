#!/usr/bin/env python3
"""会員ページのローカルプレビュー用サーバー。

    python3 serve.py

を実行して http://localhost:4322 を開いてください。停止は Control + C。
表示するのは site/ の中身です。原稿(.md)を直したら build.py を実行し直してください。
"""
import functools
import http.server
import os
import socketserver

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "site")
PORT = int(os.environ.get("PORT") or 4322)


class Handler(http.server.SimpleHTTPRequestHandler):
    """/teitaiki のような拡張子なしのURLも表示できるようにする。"""

    def translate_path(self, path):
        full = super().translate_path(path)
        if os.path.isdir(full) or os.path.isfile(full):
            return full
        if not os.path.splitext(full)[1]:
            candidate = full + ".html"
            if os.path.isfile(candidate):
                return candidate
        return full

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    os.chdir(ROOT)
    handler = functools.partial(Handler, directory=ROOT)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print("D/LIGHT 会員ページ  →  http://localhost:%d" % PORT)
        print("(停止するには Control + C)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n停止しました。")
