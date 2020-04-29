
import datetime

from peewee import Model, UUIDField, CharField, DateTimeField
from playhouse.sqlite_ext import SqliteExtDatabase
from uuid import uuid4


log = object

db = SqliteExtDatabase(None, pragmas={
    'journal_mode': 'wal',
    'cache_size': -1 * 64000,  # 64MB
    'foreign_keys': 1,
    'ignore_check_constraints': 0,
    'synchronous': 0
})


def _create_uuid():
    return str(uuid4())


def init_db(db_path: str, logger: object) -> SqliteExtDatabase:
    global log

    log = logger
    log.debug("Initializing database at: {}".format(db_path))
    db.init(db_path)
    db.create_tables([Job], safe=True)
    return db


class BaseModel(Model):
    class Meta:
        database = db


class Job(BaseModel):
    message_delim = "\n"

    statuses = [
        "NEW",
        "IN_PROGRESS",
        "SUCCESS",
        "FAILED",
    ]

    id = UUIDField(primary_key=True, default=_create_uuid)
    status = CharField(null=False)
    request = CharField(null=True)
    message = CharField(null=True)
    created = DateTimeField(default=datetime.datetime.now)

    def update_status(self, status: str):
        if status in self.statuses:
            self.status = status
            self.save()
        else:
            raise ValueError("Not a valid status: '{}'".format(status))

    def add_message(self, message: str):
        if not self.message:
            self.message = ""
        else:
            self.message += self.message_delim
        self.message += str(message)
        self.save()

    def fail_with_message(self, message: str):
        self.update_status("FAILED")
        self.add_message(message)
