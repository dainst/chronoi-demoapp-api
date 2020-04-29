
# Demo App

A small flask application that can be used to expose command line programs via a Web Api for demonstration purposes.

Features:

* Rate-limited Endpoint for scheduling jobs with optional file upload.
* Commands are configurable on project startup time.
* Delayed execution of jobs/command. (Requester has to poll for success/errors.)
* TODO: Configurable intervals and limits for housekeeping to prevent resource exhaustion.


## Basic Functionality

To run an example application, you can copy the `cmds.example.py` into a file `cmds.py` in the project directory. The `cmds.py` contains some simple command definitions like these:

```python
from src.commands import Option, FilePath

commands = [
    {
        "name": "date",
        "exec": [
            "date",
            Option("-d", to_shell="-d", nargs=1)
        ],
        "timeout": 0.5,
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
```

Once the `cmds.py` exists, you can start a development server. See [Setup](#setup) below.

The above definition would set up your demo app as a time and echo-server.

### Example: date

For example to trigger the date command you can send a POST request like the following:

```bash
curl -d '{ "text": "", "command": { "name": "date", "options": []} }' \
     localhost:8080/run
```

This will return a  json response containing a job id like the following:

```json
{
  "job": "78b360ce-1517-4c3c-8301-741fd97f9fa9"
}
```

The results of the date command executed on the remote can be retrieved with that id:

```bash
> curl localhost:8080/result/78b360ce-1517-4c3c-8301-741fd97f9fa9.stdout
Di 28. Apr 17:10:22 CEST 2020
```

### Example: cat


The app allows you to send additional text that can be used in a file argument. Using the `cat` command defined above with the text parameter the application will use the output of the `cat` program to write our results. This also illustrates the use of the "numbers" option which instructs cat to use `-n` (print line numbers).

```bash
curl -d '{ "text": "One line\nAnother line", "command": { "name": "cat", "options": [ "numbers" ]} }' \
     localhost:8080/run
```

will give an id again.

```json
{
  "job": "36c14fb4-9ec9-437a-80a9-8ffb01d13197"
}
```

The results are then at `result/<id>.stdout`, stderr is empty:

```
> curl localhost:8080/result/36c14fb4-9ec9-437a-80a9-8ffb01d13197.stdout
     1	One line
     2	Another line
> curl localhost:8080/result/36c14fb4-9ec9-437a-80a9-8ffb01d13197.stderr
```

### Example: date with options

The "-d" option in the "date" command can be used by including it in the options array together with an argument, e.g.:

```bash
> curl -d '{ "text": "", "command": { "name": "date", "options": ["-d", "yesterday"]} }' localhost:8080/run
{
  "job": "d102ca12-06d0-434e-b392-b9771c96fc38"
}
> curl localhost:8080/result/d102ca12-06d0-434e-b392-b9771c96fc38.stdout
Di 27. Apr 17:22:13 CEST 2020
```

Options are shell escaped before execution:

```bash
> curl -d '{ "text": "", "command": { "name": "date", "options": ["-d", "now; cat /etc/passwd"]} }' localhost:8080/run
{
  "job": "87ee6c4e-94b7-45ee-a08f-98579d783b7a"
}
> curl localhost:8080/result/87ee6c4e-94b7-45ee-a08f-98579d783b7a.stderr
date: invalid date ‘'now; cat /etc/passwd'’
```


## Setup

Either install [poetry locally](https://python-poetry.org/docs/) and do

```bash
poetry use 3.8
poetry install
make run
```

Or alternatively use a docker container:

```bash
make docker-build
make docker-run
```

To run the tests:

```bash
make test
```

Or alternatively using docker:

```bash
make docker-build     # if not built already
make docker-test
```

#### Configure pycharm with poetry

```bash
poetry env info
```

and use the path as the interpreter location at:

* Settings > Project > Python Interpreter > Click Cog icon right > Add
* Under "VirtualEnv Environment" > "Existing environment" > "..."
* Use the path from above, you might need to add "bin/python" to it or use a "python.exe" file under windows to mark the python executable as the environment
