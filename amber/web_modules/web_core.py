# coding=utf-8
import asyncio
import webbrowser
import logging
import os
import sys
import time
from random import randint

from flask import Flask, render_template_string, send_from_directory, request
from amber.web_modules.sockets import Socket
from amber.web_modules.web_utils import threaded


MODULE_DIR = os.path.abspath(os.path.dirname(__file__))
FRONTEND_DIR = os.path.join(MODULE_DIR, "..", "frontend")

GAME_DIR = os.path.dirname(sys.argv[0])
print("\n\nHMM INDEED: {}\n\n".format(GAME_DIR))

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
    with open(os.path.join(FRONTEND_DIR, "index.html"), "r") as file:
        return render_template_string(file.read(), host=HOST, port=SOCKET_PORT)


# ONLY FOR DEVELOPMENT!
@app.after_request
def add_header(r):
    """
    Removes caching
    """
    if request.path != "/":
        return r

    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    # r.headers['Cache-Control'] = 'public, max-age=0'
    return r


@app.route("/<path:url>")
def simplify(url: str):
    if url.startswith(("assets/", "/assets")):
        l_path, filename = os.path.split(url)
        return send_from_directory(os.path.join(FRONTEND_DIR, l_path), filename)
    else:
        f_path, fn = os.path.split(os.path.join(GAME_DIR, url))
        log.info("\nHMMMMMM2\n{}, {}\n{}".format(f_path, fn, os.path.join(FRONTEND_DIR, f_path)))
        log.info("ISFILE2: {}\n\n".format(os.path.isfile(os.path.join(FRONTEND_DIR, f_path, fn))))
        return send_from_directory(f_path, fn)


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