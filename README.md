
# Demo App

A small flask application that can be used to expose command line programs via a Web Api for demonstration purposes.

Features:

* API for file upload
* Configurable commands with proper option checking.
* Delayed execution via a scheduler.
* TODO: Rate-limited endpoints.
* TODO: Automatic housekeeping for removing stale files and jobs.


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
