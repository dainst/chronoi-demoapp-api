#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
import time
import unittest

from io import BytesIO

from app import app
from files import upload_path
from models import Job

# A regex to check for uuids in different versions, but
# not allowing the null uuid
UUID_REGEX = re.compile('^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$')

# How long to wait for a task to assume to be completed
# from it's being saved in the db (in seconds)
JOB_COMPLETION_TIME = 0.5


class ApiTest(unittest.TestCase):

    def setUp(self) -> None:
        app.testing = True
        app.debug = True
        self.app = app.test_client()

    def post_json(self, route: str, data: dict):
        data = json.dumps(data)
        return self.app.post(route, json=data)

    def post_file(self, route: str, file: BytesIO, additional_content=None):
        data = {"file": (file, "test_file.ext")}
        if additional_content is not None:
            data["data"] = json.dumps(additional_content)
        return self.app.post(route, data=data)


class RouteRunTest(ApiTest):

    def test_run_text(self):
        command = {"name": "ls", "options": ["all", "long"]}
        response = self.post_json("/run", {"text": "Some text here.", "command": command})
        data = response.get_json()
        assert response.status_code == 200, "Should return 200 OK on running with text."
        assert UUID_REGEX.match(data["job"]), "Should return a uuid as job id."

    def test_run_file(self):
        data = {"command": {"name": "ls", "options": ["all", "long"]}}
        response = self.post_file("/run", BytesIO(b'File content'), additional_content=data)
        data = response.get_json()
        assert response.status_code == 200, "Should return 200 OK on running with file."
        assert UUID_REGEX.match(data["job"]), "Should return a uuid as a job id."

    def test_uploading_zero_content_file_errors(self):
        pass

    def test_uploading_a_big_file_should_be_prohibited(self):
        pass


class RouteResultTest(ApiTest):

    default_request = {
        "text": "Some\n input\n text\n",
        "command": {
            "name": "cat",
            "options": [],
        }
    }

    @classmethod
    def _prepare_job(cls, prepare_file=True) -> Job:
        # prepare a job for the database that should have been
        # executed after a while
        request = cls.default_request
        job = Job(status="NEW", request=json.dumps(request))

        # prepare the file that would have been created on job
        # upload
        if prepare_file:
            with open(upload_path(job), mode="w") as file:
                file.write(request["text"])

        return job

    @staticmethod
    def _route(job_id, stderr=False):
        template = "/result/{}.{}"
        if stderr:
            return template.format(job_id, "stderr")
        else:
            return template.format(job_id, "stdout")

    def test_scheduled_job_result(self):
        job = self._prepare_job()
        job.save(force_insert=True)

        time.sleep(JOB_COMPLETION_TIME)

        # test the stdout path
        result = self.app.get(self._route(job.id))
        assert result.status_code == 200,\
            "Should give 200 OK on result request."
        assert str(result.data, encoding="utf-8") == self.default_request["text"],\
            "Should return input text on successful cat job."

        # test the stderr path
        result = self.app.get(self._route(job.id, stderr=True))
        assert result.status_code == 200,\
            "Should give 200 OK on scheduled result stderror request."

        assert len(result.data) == 0,\
            "Should return empty stderr on successful cat job."

    def test_schedule_job_with_option_works(self):
        pass

    def test_scheduled_job_with_wrong_name_errors(self):
        pass

    def test_scheduled_job_witout_command_errors(self):
        pass

    def test_scheduled_job_with_invalid_option_errors(self):
        pass

    def test_filename_param_cannot_escape_download_dir(self):
        # route = self._route("../../../../../etc/passwd ")
        pass


if __name__ == "__main__":
    unittest.main()
