# -*- coding: utf-8 -*-

import shlex
from subprocess import run
from . import files
from .models import Job

config = {}

log = object()


def init_commands(app_config, app_logger):
    global config
    global log
    config = app_config
    log = app_logger


class Option:

    def __init__(self, name: str, to_shell, nargs=0, args_escape=shlex.quote, fail_if_missing=False):
        self.name = name
        self.to_shell = to_shell
        self.nargs = nargs
        self.args_escape = args_escape
        self.fail_if_missing = fail_if_missing

    def consume(self, args: [str]) -> [str]:
        out_args = []

        if self.name in args:
            idx = args.index(self.name)

            # put the option argument itself on the result
            out_args.append(self.to_shell)
            try:
                # collect option strings and put them on the result
                for option_arg in args[(idx + 1):(idx + 1 + self.nargs)]:
                    out_args.append(self.args_escape(option_arg))
            except ValueError:
                raise ValueError(
                    "Wrong argument count for option '{}': {}".format(self.name, self.nargs))

            # delete the consumed options
            del args[idx:idx + 1 + self.nargs]
        elif self.fail_if_missing:
            raise ValueError("Missing option '{}'".format(self.name))

        return out_args


class FilePath:

    def __init__(self, fail_if_empty=True):
        self.fail_if_empty = fail_if_empty


def execute_command(name: str, options: [str], job: Job):
    stdout = open(files.result_path_stdout(job), "wb")
    stderr = open(files.result_path_stderr(job), "wb")
    try:
        job_input_file = files.upload_path(job)
        args = _prepare_command_args(name, options, job_input_file)

        job.update_status("IN_PROGRESS")
        log.debug("Executing: '{}'".format(" ".join(args)))
        run(args,
            stdout=stdout,
            stderr=stderr,
            check=True,
            timeout=_command_timeout(name))
        job.update_status("SUCCESS")
    # This catches errors from our program as well as from the called
    # process, since the latter are wrapped as subprocess.SubprocessError
    except Exception as e:
        job.update_status("FAILED")
        job.add_message(str(e))
    finally:
        stdout.close()
        stderr.close()


def _prepare_command_args(cmd_name: str, cmd_options: [str], job_file_path="") -> [str]:
    args = []
    command_def = _get_command_def(cmd_name)

    for exec_elem in command_def["exec"]:
        if isinstance(exec_elem, str):
            args.append(exec_elem)
        elif isinstance(exec_elem, Option):
            args += exec_elem.consume(cmd_options)
        elif isinstance(exec_elem, FilePath):
            args.append(job_file_path)

    # There should be no user defined options left at this point
    if len(cmd_options) > 0:
        raise ValueError("Some options were not handled.")

    return args


def _get_command_def(name: str):
    for command in commands:
        if command["name"] == name:
            return command
    raise ValueError("Not a command name: {}".format(name))


def _command_timeout(cmd_name: str) -> float:
    cmd_def = _get_command_def(name=cmd_name)
    if "timeout" in cmd_def:
        timeout = cmd_def.get("timeout")
    else:
        timeout = config.get("DEFAULT_CMD_TIMEOUT", 1.0)
    return float(timeout)

example_commands = [
    {
        "name": "ls",
        "exec": [
            "ls",
            Option("all", to_shell="-a"),
            Option("long", to_shell="-l")
        ],
        "timeout": 1.5,
    },
    {
        "name": "cat",
        "exec": [
            "cat",
            Option("numbers", to_shell="-n"),
            FilePath()
        ],
        "timeout": 5.0,
    }
]

commands = example_commands
