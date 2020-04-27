#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, json, send_from_directory

import logging
import os

import src.files as files
from src.models import init_db, Job
from src.commands import init_commands
from src.schedule import init_app_scheduler


project_dir = os.path.dirname(__file__)

config_dir = os.path.join(project_dir, "config")

app = Flask(__name__)

db = None

log = app.logger


def init():
    # adjust the global log level
    if app.config["ENV"] != "production":
        log.setLevel(logging.DEBUG)
    # Consume config files
    _init_configs()
    # Setup all necessary directories (needs config)
    files.init_file_structure(app_config=app.config, proj_dir=project_dir, logger=app.logger)
    # Setup the database (needs file structure, config)
    init_db(files.db_path(), log)
    # Setup the commands module (needs config)
    init_commands(app_config=app.config, app_logger=app.logger)
    # Setup the scheduler and directly start it (needs db, commands)
    scheduler = init_app_scheduler(app_config=app.config, app_logger=app.logger)
    scheduler.start()


def _consume_config_file(filename: str):
    config_path = os.path.join(config_dir, filename)
    app.config.from_pyfile(config_path)


# consume the config files in order of precedence
def _init_configs():
    _consume_config_file("default.cfg")

    # read the config file appropriate for this environment
    if app.config.get("ENV") in ["testing", "development", "production"]:
        _consume_config_file("{}.cfg".format(app.config.get("ENV")))
    else:
        log.warning("Non-standard environment name: {}".format(app.config.get("ENV")))

    # Enable file sending via X-Sendfile if that is wished for
    if app.config.get("USE_X_SENDFILE", False):
        app.use_x_sendfile = True

    # The user may specify a path to different env file:
    if os.environ.get("FLASK_APP_CONFIG", ""):
        app.config.from_envvar("FLASK_APP_CONFIG")


init()


@app.route("/run", methods=["POST"])
def handle_run():

    job = Job(status="NEW")
    filename = files.upload_path(job)
    log.debug("Writing to: " + filename)

    if request.mimetype == "multipart/form-data":
        # Handle a run command with accompanying file upload
        # Write the file to disk and save the json formatted
        # command definition for later processing
        file = request.files['file']
        file.save(filename)
        job.request = request.form.get("data")
    else:
        # Handle a run command with text input. Save the text
        # to a file and save the command definition for later
        # processing
        data = json.loads(request.get_json())
        with open(filename, mode="w", encoding="UTF-8") as file:
            file.write(data["text"])
        del data["text"]
        job.request = json.dumps(data)

    job.save(force_insert=True)
    return {"job": job.id}


@app.route("/result/<path:filename>")
def handle_result(filename):
    return send_from_directory(files.downloads_dir(), filename)


def get_status():
    pass


if __name__ == "__main__":
    app.run(port=8080, debug=True)
