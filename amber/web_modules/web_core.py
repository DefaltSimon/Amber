# coding=utf-8
import asyncio
import webbrowser
import logging
import os

from flask import Flask, render_template_string, send_from_directory
from amber.web_modules.sockets import Socket
from amber.web_modules.web_utils import threaded


MODULE_DIR = os.path.dirname(__file__)
FRONTEND_DIR = os.path.join(MODULE_DIR, "..", "frontend")

with open(os.path.join(FRONTEND_DIR, "index.html"), "r") as file:
    MAIN_TEMPLATE = file.read()

HOST = "localhost"
FLASK_PORT = 8566
SOCKET_PORT = 8567
GAME_NAME = "testing"

app = Flask(__name__)
loop = asyncio.get_event_loop()
# socket = Socket(loop, HOST, SOCKET_PORT)

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


@app.route("/")
def main_page():
    temp = render_template_string(MAIN_TEMPLATE, host=HOST, port=SOCKET_PORT, name=GAME_NAME)
    return temp


@app.route("/assets/<path:url>")
def simplify(url):
    l_path, filename = str(url).rsplit("/", maxsplit=1)
    return send_from_directory(os.path.join("frontend", "assets", l_path), filename)


@threaded
def _run_flask():
    app.run(debug=False, host=HOST, port=FLASK_PORT)


def run_web(amber_inst, open_browser=True):
    log.info("Starting web module...")
    try:
        _run_flask()
        socket = Socket(amber_inst, loop, HOST, SOCKET_PORT)

        if open_browser:
            page_url = "http://{}:{}".format(HOST, FLASK_PORT)
            webbrowser.open(page_url)

        loop.create_task(socket.start())
        loop.run_forever()
    except:
        log.critical("Loop exception raised, exiting")
        raise