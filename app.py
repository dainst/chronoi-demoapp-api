#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask

from config import config

from models import init_db


app = Flask(__name__)


db = None


@app.route("/run", methods=["POST"])
def run():
    from models import Job

    job = Job(status="NEW")
    job.save(force_insert=True)

    return {"job": job.id}


def get_status():
    pass


if __name__ == "__main__":
    init_db(config.dev.DB_FILE)
    app.run(port=8080, debug=True)
