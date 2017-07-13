# coding=utf-8
import asyncio
import webbrowser
import logging
import os
import time
from random import randint

from flask import Flask, render_template_string, send_from_directory
from amber.web_modules.sockets import Socket
from amber.web_modules.web_utils import threaded


MODULE_DIR = os.path.dirname(__file__)
FRONTEND_DIR = os.path.join(MODULE_DIR, "..", "frontend")

with open(os.path.join(FRONTEND_DIR, "index.html"), "r") as file:
    MAIN_TEMPLATE = file.read()

HOST = "localhost"
FLASK_PORT = randint(8560, 8566)
SOCKET_PORT = randint(8567, 8573)

app = Flask(__name__)
loop = asyncio.get_event_loop()
# socket = Socket(loop, HOST, SOCKET_PORT)

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

logging.getLogger("werkzeug").setLevel(logging.WARNING)


@app.route("/")
def main_page():
    return render_template_string(MAIN_TEMPLATE, host=HOST, port=SOCKET_PORT)


@app.route("/assets/<path:url>")
def simplify(url):
    l_path, filename = str(url).rsplit("/", maxsplit=1)
    return send_from_directory(os.path.join(FRONTEND_DIR, "assets", l_path), filename)


@threaded
def _run_flask():
    app.run(debug=False, host=HOST, port=FLASK_PORT)


def run_web(amber_inst, open_browser=True):

    try:
        log.info("Starting flask server...")
        _run_flask()
        log.info("Flask server running")

        socket = Socket(amber_inst, loop, HOST, SOCKET_PORT)
        page_url = "http://{}:{}".format(HOST, FLASK_PORT)

        # no async here
        @threaded
        def open_br():
            time.sleep(1)
            webbrowser.open(page_url)

        if open_browser:
            open_br()
        log.info("Serving to {}".format(page_url))

        loop.create_task(socket.start(amber_inst))
        loop.run_forever()
    except:
        log.critical("Loop exception raised, exiting")
        raise