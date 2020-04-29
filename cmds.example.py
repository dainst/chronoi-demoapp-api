
from src.commands import Option, FilePath

example_commands = [
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

commands = example_commands
