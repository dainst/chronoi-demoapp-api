
# Demo App

A small flask application that can be used to expose command line programs via a Web Api for demonstration purposes.

Features:

* Rate-limited Endpoint for scheduling jobs with optional file upload.
* Commands are configurable on project startup time.
* Delayed execution of jobs/command. (Requester has to poll for success/errors.)
* TODO: Configurable intervals and limits for housekeeping to prevent resource exhaustion.


## Development

To start a dev version run:

```bash
make run
```

To run the tests run:

```bash
make test
```

#### Configure pycharm with poetry

```bash
poetry env info
```

and use the path as the interpreter location at:

* Settings > Project > Python Interpreter > Click Cog icon right > Add
* Under "VirtualEnv Environment" > "Existing environment" > "..."
* Use the path from above, you might need to add "bin/python" to it or use a "python.exe" file under windows to mark the python executable as the environment
