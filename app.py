#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, json, send_from_directory, make_response
from peewee import DoesNotExist

import argparse
import flask_limiter
import flask_limiter.util
import logging
import os

import src.files as files
from src.models import init_db, Job
from src.commands import init_commands
from src.schedule import init_app_scheduler

# The user defined command definitions are imported here
# If you get an error, that this is undefined, you probably
# want to copy the cmds.example.py to cmds.py in the project
# directory.
from cmds import commands

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
    init_db(db_path=files.db_path(), logger=log)
    # Setup the commands module (needs config)
    init_commands(app_config=app.config, app_logger=app.logger, commands_list=commands)
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


def _init_rate_limiter() -> flask_limiter.Limiter:
    # Ask the config if the http header or the actual ip address
    # should be used, when identifying users for rate limiting.
    if app.config.get("RATE_LIMITING_USE_X_FORWARDED_FOR"):
        key_func = flask_limiter.util.get_ipaddr
    else:
        key_func = flask_limiter.util.get_remote_address
    return flask_limiter.Limiter(app, key_func=key_func)


def _rate_limit_for_job_request() -> "":
    return app.config.get("RATE_LIMIT_JOB_REQUESTS")


# Return a json response instead of the default html for a
# rate limited response.
@app.errorhandler(429)
def ratelimit_handler(e):
    return make_response(json.jsonify(limit="%s" % e.description), 429)


init()

limiter = _init_rate_limiter()


@app.route("/run", methods=["POST"])
@limiter.limit(_rate_limit_for_job_request)
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
        data = json.loads(request.form.get("data"))
    else:
        # Handle a run command with text input. Save the text
        # to a file and save the command definition for later
        # processing
        data = json.loads(request.get_data())
        with open(filename, mode="w", encoding="UTF-8") as file:
            file.write(data["text"])

    # delete any text or additional arguments before saving the request
    for k in list(data.keys()):
        if k not in ["command"]:
            del data[k]
    job.request = json.dumps(data)
    job.save(force_insert=True)
    return {"job": job.id}


@app.route("/result/<path:filename>")
def handle_result(filename):
    return send_from_directory(files.downloads_dir(), filename)


@app.route("/status/<jobId>")
def handle_status(jobId):
    try:
        job = Job.get_by_id(jobId)
        return {
            "id": job.id,
            "status": job.status,
            "message": job.message
        }
    except DoesNotExist:
        return {"message": "A job with this id does not exist."}, 404


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Start the demoapp server.")
    parser.add_argument("--port", type=int, default=8080, help="The local port to expose the api at.")
    args = parser.parse_args()

    app.run(port=args.port, host="0.0.0.0")
