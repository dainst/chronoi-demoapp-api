#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

import os
import re

import unittest

from app import app
from models import init_db
from config import config


_uuid_regex = re.compile('^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$')


class ApiTest(unittest.TestCase):

    def setUp(self) -> None:
        self._setupNewDb(config.test.DB_FILE)
        app.testing = True
        self.app = app.test_client()

    @staticmethod
    def _setupNewDb(path):
        if os.path.exists(path):
            os.remove(path)
        init_db(path)

    def post_json(self, route: str, data: dict):
        data = json.dumps(data)
        return self.app.post(route, data=data)

    def test_run_text(self):
        response = self.post_json("/run", {"text": "Some text here."})
        data = response.get_json()
        assert _uuid_regex.match(data["job"]), "Should return a uuid as job id."


if __name__ == "__main__":
    unittest.main()
