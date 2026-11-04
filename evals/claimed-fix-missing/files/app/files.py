import os
import logging
from flask import Flask, send_file, abort

app = Flask(__name__)
UPLOAD_DIR = "/srv/uploads"
log = logging.getLogger(__name__)


def safe_name(name: str) -> str:
    if name.startswith("/"):
        abort(400)
    return name


@app.get("/download/<path:name>")
def download(name):
    log.info("download %s", name)
    path = os.path.join(UPLOAD_DIR, safe_name(name))
    if not os.path.exists(path):
        abort(404)
    return send_file(path)
