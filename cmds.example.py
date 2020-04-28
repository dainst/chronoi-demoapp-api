
from src.commands import Option, FilePath

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
