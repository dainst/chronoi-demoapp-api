#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
import unittest

from io import BytesIO

from app import app


_uuid_regex = re.compile('^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$')


class ApiTest(unittest.TestCase):

    def setUp(self) -> None:
        app.testing = True
        app.debug = True
        self.app = app.test_client()

    def post_json(self, route: str, data: dict):
        data = json.dumps(data)
        return self.app.post(route, json=data)

    def post_file(self, route: str, file: BytesIO):
        data = {"file": (file, "test_file.ext")}
        return self.app.post(route, data=data)

    def test_run_text(self):
        response = self.post_json("/run", {"text": "Some text here."})
        data = response.get_json()
        assert _uuid_regex.match(data["job"]), "Should return a uuid as job id."

    def test_run_file(self):
        response = self.post_file("/run", BytesIO(b'File content'))
        data = response.get_json()
        assert response.status_code == 200, "Should return 200 OK on file upload."
        assert _uuid_regex.match(data["job"]), "Should return a uuid as a job id."

    def test_uploading_zero_content_file_errors(self):
        pass

    def test_uploading_a_big_file_should_be_prohibited(self):
        pass


if __name__ == "__main__":
    unittest.main()
