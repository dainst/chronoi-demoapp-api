
from datetime import datetime, timedelta
from flask import json
from apscheduler.schedulers.background import BackgroundScheduler
from peewee import DoesNotExist


from .models import Job
from .commands import execute_command


config = {}

log = object()

dir_uploads = "/invalid/path"
dir_downloads = "/invalid/path"


def task_run_new_job():
    job = None
    try:
        job = Job.get(Job.status == "NEW")
        request = json.loads(job.request)
        execute_command(name=request["command"]["name"],
                        options=request["command"]["options"],
                        job=job)
    except DoesNotExist:
        # No jobs to execute
        pass
    except KeyError as e:
        log.error("Failing job with with key error: {}".format(e))
        if job:
            job.fail_with_message("Key error: {}".format(e))
    except Exception as e:
        # Since command execution has it's own error handling,
        # this should catch all errors during preparation of the command.
        msg = "Unexpected error in command preparation: {}".format(e)
        log.error(msg)
        if job:
            job.fail_with_message(msg)


def task_cleanup_old_job():
    max_seconds = config.get("TIME_JOB_KEEP_IN_DB")
    max_datetime = datetime.now() - timedelta(seconds=max_seconds)

    try:
        job = Job.select() \
                .where(Job.created < max_datetime) \
                .order_by(Job.created.asc()) \
                .get()
        log.debug("Deleting old job with creation time: {}".format(job.created))
        job.delete_instance()
    except DoesNotExist:
        # No jobs to delete
        pass
    except Exception as e:
        log.error("Error when removing job: {}".format(e))


_jobs_to_config_values = [
    (task_run_new_job, "INTERVAL_JOB_START"),
    (task_cleanup_old_job, "INTERVAL_CLEANUP_START"),
]


def init_app_scheduler(app_config, app_logger) -> BackgroundScheduler:
    global log
    global config
    config = app_config
    log = app_logger

    scheduler = BackgroundScheduler()

    for func, config_key in _jobs_to_config_values:
        seconds = config.get(config_key)
        log.debug("Scheduling func {} with interval: {}s.".format(func.__name__, seconds))
        scheduler.add_job(func, trigger='interval', coalesce=True, seconds=seconds)

    return scheduler
