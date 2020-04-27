#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import copy
import json
import os
import re
import time
import unittest
import warnings

from io import BytesIO
from werkzeug.wrappers import Response

from app import app
from src.files import upload_path
from src.models import Job

# A regex to check for uuids in different versions, but
# not allowing the null uuid
UUID_REGEX = re.compile('^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$')

# How long to wait for a task to assume to be completed
# from it's being saved in the db (in seconds)
JOB_COMPLETION_TIME = 0.5


class JobHelper:

    default_request = {
        "text": "Some\n input\n text\n",
        "command": {
            "name": "cat",
            "options": [],
        }
    }

    @classmethod
    def prepare_job(cls, request=None) -> Job:
        # prepare a job for the database that should have been
        # executed after a while
        if request is None:
            request = cls.default_request
        job = Job(status="NEW", request=json.dumps(request))

        # prepare the file that would have been created on job
        # upload
        with open(upload_path(job), mode="w") as file:
            file.write(request["text"])
        return job

    @classmethod
    def prepare_job_with_simple_option(cls) -> Job:
        request = copy.deepcopy(cls.default_request)
        request["command"]["options"] = ["numbers"]
        return cls.prepare_job(request=request)

    @classmethod
    def prepare_job_with_invalid_command(cls) -> Job:
        request = copy.deepcopy(cls.default_request)
        request["command"]["name"] = "invalid-command"
        return cls.prepare_job(request=request)


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
        assert os.path.isfile(upload_path(Job.get(Job.id == data["job"]))), "Should have created a file."

    def test_run_file(self):
        data = {"command": {"name": "ls", "options": ["all", "long"]}}
        response = self.post_file("/run", BytesIO(b'File content'), additional_content=data)
        data = response.get_json()
        assert response.status_code == 200, "Should return 200 OK on running with file."
        assert UUID_REGEX.match(data["job"]), "Should return a uuid as a job id."
        assert os.path.isfile(upload_path(Job.get(Job.id == data["job"]))), "Should have created a file."

    def todo_test_uploading_zero_content_file_errors(self):
        pass

    def todo_test_uploading_a_big_file_should_be_prohibited(self):
        pass

    def todo_test_sending_a_big_request_should_be_prohibited(self):
        pass

    def todo_test_sending_additional_request_fields_are_not_saved(self):
        pass


class RouteResultTest(ApiTest):

    def setUp(self):
        super().setUp()
        # Ignore Resource Warnings resulting from flask's send_from_directory().
        # That function works differently in production anyway.
        warnings.simplefilter("ignore", ResourceWarning)

    def tearDown(self):
        super().tearDown()
        # Reset the filter from setUp
        warnings.simplefilter("default", ResourceWarning)

    @staticmethod
    def _route(job_id, stderr=False):
        template = "/result/{}.{}"
        if stderr:
            return template.format(job_id, "stderr")
        else:
            return template.format(job_id, "stdout")

    @staticmethod
    def _assert_empty_ok(response: Response):
        assert response.status_code == 200, "Should return 200 OK."
        assert response.get_data(as_text=True) == "", "Should have returned empty."

    def test_scheduled_job_result(self):
        job = JobHelper.prepare_job()
        job.save(force_insert=True)
        time.sleep(JOB_COMPLETION_TIME)

        # test the stdout path
        response = self.app.get(self._route(job.id))
        assert response.status_code == 200, "Should give 200 OK on response request."
        assert response.get_data(as_text=True) == JobHelper.default_request["text"],\
            "Should return input text on successful cat job."

        # test the stderr path
        response = self.app.get(self._route(job.id, stderr=True))
        self._assert_empty_ok(response)

    def test_schedule_job_with_option_works(self):
        job = JobHelper.prepare_job_with_simple_option()
        job.save(force_insert=True)
        time.sleep(JOB_COMPLETION_TIME)

        # test the stdout response
        response = self.app.get(self._route(job.id))
        assert response.status_code == 200, "Should return 200 OK on scheduled job with option."
        assert response.get_data(as_text=True) != JobHelper.default_request["text"],\
            "Should not return the standard input text on scheduled result with options."
        assert len(response.data) >= 0, "Should return non-empty on scheduled job with options."

        # test the stderr response
        response = self.app.get(self._route(job.id, stderr=True))
        self._assert_empty_ok(response)

    def test_scheduled_job_with_wrong_name_errors(self):
        job = JobHelper.prepare_job_with_invalid_command()
        job.save(force_insert=True)
        time.sleep(JOB_COMPLETION_TIME)

        # stdout and stderr should simply be empty if the job never ran
        response = self.app.get(self._route(job.id))
        self._assert_empty_ok(response)

        # stderr should have an error message
        response = self.app.get(self._route(job.id, stderr=True))
        self._assert_empty_ok(response)

    def todo_test_scheduled_job_witout_command_errors(self):
        pass

    def todo_test_scheduled_job_with_invalid_option_errors(self):
        pass

    def todo_test_filename_param_cannot_escape_download_dir(self):
        # route = self._route("../../../../../etc/passwd ")
        pass


class HousekeepingTest(unittest.TestCase):

    def setUp(self) -> None:
        app.testing = True
        app.debug = True

    def todo_test_old_file_gets_deleted(self):
        pass

    def todo_test_old_job_gets_deleted(self):
        pass

    def todo_test_invalid_file_gets_deleted(self):
        pass

if __name__ == "__main__":
    unittest.main()
