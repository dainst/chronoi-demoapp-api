
import atexit
import os
import shutil
import tempfile

from models import Job


project_dir = "/tmp/does/not/exist/"

test_dir = "/tmp/does/not/exist/"

# The app's config
config = {}

# The app's logger
log = object()


def db_path():
    return _project_path(config.get("DB_FILE"))


def uploads_dir():
    return _project_path(config.get("DIR_UPLOADS"))


def downloads_dir():
    return _project_path(config.get("DIR_DOWNLOADS"))


def upload_path(job: Job):
    return os.path.join(uploads_dir(), str(job.id))


def result_path_stdout(job: Job):
    return _result_path(job, ".stdout")


def result_path_stderr(job: Job):
    return _result_path(job, ".stderr")


def _result_path(job: Job, postfix: str) -> str:
    file_path = str(job.id) + postfix
    return os.path.join(downloads_dir(), file_path)


def init_file_structure(app_config, proj_dir, logger):
    global config
    global project_dir
    global log
    config = app_config
    project_dir = proj_dir
    log = logger

    _init_directories()


def _project_path(path: str) -> str:
    """
    # Convenience method to generate a project path depending on
    # the environment and whether the path is already absolute.
    # If the input is an absolute path it will be returned unchanged

    :param path: An absolute or relative path.
    :return: Always returns an absolute path.
    """
    if not os.path.isabs(path):
        # if the path is not absolute it is either bound to
        # the test
        if config["ENV"] == "testing":
            result = os.path.join(test_dir, path)
        else:
            result = os.path.join(project_dir, path)
    else:
        # if a path is already absolute, return it
        result = path
    return result


def _config_project_path(name: str) -> str:
    """
    Convenience method to query a project path from the app
    config, taking

    :param name: Name of the config variable to query
    :return: An absolute path.
    """
    return _project_path(config.get(name))


def _init_project_dir(dir_path: str):
    directory = _project_path(dir_path)
    os.makedirs(directory, exist_ok=True)
    log.debug("Creating/Using dir: {}".format(directory))


def _init_directories():
    global test_dir

    # create a test directory
    if config["ENV"] == "testing":
        test_dir = tempfile.mkdtemp(prefix="demoapp-testing")
        # register the deletion of the tempdir on program exit
        # atexit.register(_delete_test_directory)

    for key in ["DIR_UPLOADS", "DIR_DOWNLOADS"]:
        _init_project_dir(config.get(key))


def _delete_test_directory():
    if os.path.isdir(test_dir):
        shutil.rmtree(test_dir)
