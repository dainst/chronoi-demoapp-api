
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
example_commands = [
    {
        "name": "date",
        "exec": [
            "date",
            Option("other", to_shell="-d", nargs=1)
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

Once the `cmds.py` exists, you can start a development server with:

```bash
make run
```

The above definition would set up your demo app as a time and echo-server. For example to trigger the date command you can send a POST request like the following:

```bash
curl -H "Content-Type: application/json" \
     -d '{ "text": "", "command": { "name": "date", "options": []} }' \
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
$ curl localhost:8080/result/676587c3-3ae5-40f8-800a-f583ae0ed922.stdout
Di 28. Apr 17:10:22 CEST 2020
```

The app allows you to send additional text that can be used in a file argument. Using the `cat` command defined above with the text parameter the application will use the output of the `cat` program to write our results. This also illustrates the use of the "numbers" option which instructs cat to use `-n` (print line numbers).

```bash
curl -H "Content-Type: application/json" \
     -d '{ "text": "One line\nAnother line", "command": { "name": "cat", "options": [ "numbers" ]} }' \
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
$ curl localhost:8080/result/36c14fb4-9ec9-437a-80a9-8ffb01d13197.stdout
     1	One line
     2	Another line
$ curl localhost:8080/result/36c14fb4-9ec9-437a-80a9-8ffb01d13197.stderr
```

## Development

Simple setup

```bash
poetry use 3.8
poetry install
make run
```

To run the tests:

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
