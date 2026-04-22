"""Entrypoint. Creates the webview window with the HTML UI and Api bridge."""
import os
import sys

import webview

from api import Api
from progress import get_dispatcher


def ui_path():
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, "ui", "index.html")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui", "index.html")


def main():
    api = Api()
    html = ui_path()
    if not os.path.exists(html):
        sys.stderr.write(f"UI missing: {html}\n")
        sys.exit(2)

    window = webview.create_window(
        title="Storage Cleaner",
        url=html,
        js_api=api,
        width=1200,
        height=820,
        min_size=(960, 640),
        background_color="#0f1115",
        text_select=True,
    )

    def on_ready():
        api.window = window
        get_dispatcher().attach(window)

    webview.start(on_ready, debug=False)


if __name__ == "__main__":
    main()
