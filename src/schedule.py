
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
        log.debug("No jobs to execute.")
    except KeyError as e:
        if job:
            job.add_message("Key error: {}".format(e))


_jobs_to_config_values = [
    (task_run_new_job, "INTERVAL_JOB_START"),
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
