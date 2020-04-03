
import datetime

from peewee import Model, UUIDField, CharField, DateTimeField
from playhouse.sqlite_ext import SqliteExtDatabase
from uuid import uuid4


db = SqliteExtDatabase(None, pragmas={
    'journal_mode': 'wal',
    'cache_size': -1 * 64000,  # 64MB
    'foreign_keys': 1,
    'ignore_check_constraints': 0,
    'synchronous': 0
})


def _create_uuid():
    return str(uuid4())


def init_db(db_path: str) -> SqliteExtDatabase:
    db.init(db_path)
    db.create_tables([Job], safe=True)
    return db


class BaseModel(Model):
    class Meta:
        database = db


class Job(BaseModel):
    id = UUIDField(primary_key=True, default=_create_uuid)
    status = CharField()
    created = DateTimeField(default=datetime.datetime.now)
