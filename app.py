#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, json

import atexit
import logging
import os
import shutil
import tempfile

from models import init_db, Job

appname = "demoapp"

project_dir = os.path.dirname(__file__)

config_dir = os.path.join(project_dir, "config")

test_dir = "/tmp/does/not/exist/"


def _init():
    # Consume config files
    _init_configs()
    # init the logger
    if app.config["ENV"] != "production":
        log.setLevel(logging.DEBUG)
    # Setup all necessary directories
    _init_directories()
    # Setup the database possibly inside one of the directories
    init_db(_project_path(app.config.get("DB_FILE")))


def _consume_config_file(filename: str):
    config_path = os.path.join(config_dir, filename)
    app.config.from_pyfile(config_path)


# Convenience method to generate a project path depending on
# the environment and whether the path is already absolute.
# Always returns an absolute path.
def _project_path(path: str) -> str:
    if not os.path.isabs(path):
        # if the path is not absolute it is either bound to
        # the test
        if app.config["ENV"] == "testing":
            result = os.path.join(test_dir, path)
        else:
            result = os.path.join(project_dir, path)
    else:
        # if a path is already absolute, return it
        result = path
    return result


# consume the config files in order of precedence
def _init_configs():
    _consume_config_file("default.cfg")

    # read the config file appropriate for this environment
    if app.config.get("ENV") in ["testing", "development", "production"]:
        _consume_config_file("{}.cfg".format(app.config.get("ENV")))
    else:
        log.warning("Non-standard environment name: {}".format(app.config.get("ENV")))

    # The user may specify a path to different env file:
    if os.environ.get("FLASK_APP_CONFIG", ""):
        app.config.from_envvar("FLASK_APP_CONFIG")


def _init_project_dir(dir_path: str):
    directory = _project_path(dir_path)
    os.makedirs(directory, exist_ok=True)
    log.debug("Creating/Using dir: {}".format(directory))


def _init_directories():
    global test_dir

    if app.config["ENV"] == "testing":
        name = appname + "-testing"
        test_dir = tempfile.mkdtemp(prefix=name)
        # register the deletion of the tempdir on exit
        atexit.register(_delete_test_directory)

    for key in ["DIR_UPLOADS", "DIR_DOWNLOADS"]:
        _init_project_dir(app.config[key])


def _delete_test_directory():
    if os.path.isdir(test_dir):
        shutil.rmtree(test_dir)


app = Flask(__name__)

db = None

log = app.logger

_init()


def _uploads_path(job: Job) -> str:
    folder = _project_path(app.config.get("DIR_UPLOADS"))
    return os.path.join(folder, job.id)


@app.route("/run", methods=["POST"])
def run():

    job = Job(status="NEW")
    job.save(force_insert=True)

    filename = _uploads_path(job)
    log.debug("Writing to: " + filename)

    if request.mimetype == "multipart/form-data":
        file = request.files['file']
        file.save(filename)
    else:
        data = json.loads(request.get_json())
        with open(filename, mode="w", encoding="UTF-8") as file:
            file.write(data["text"])

    return {"job": job.id}


def get_status():
    pass


if __name__ == "__main__":
    app.run(port=8080, debug=True)
