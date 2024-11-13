import enum

import databases
import ormar
import sqlalchemy

import settings

engine = sqlalchemy.create_engine(
    url=settings.DATABASE_URL,
)

metadata = sqlalchemy.MetaData(bind=engine)

database = databases.Database(url=settings.DATABASE_URL)

model_config = ormar.OrmarConfig(
    database=database,
    engine=engine,
    metadata=metadata,
)


class TaskStatuses(enum.Enum):
    WAITING = 'ожидает выполнения'
    COMPLETED = 'завершена'
    REMOVED = 'отменена'


class Task(ormar.Model):
    ormar_config = model_config.copy(
        tablename='tasks'
    )

    id = ormar.Integer(
        primary_key=True,
        autoincrement=True,
        nullable=False,
        minimum=1,
    )

    task = ormar.String(
        nullable=False,
        max_length=100,
    )

    priority = ormar.Integer(
        minimum=1,
        maximum=5,
        default=1,
    )

    deadline = ormar.DateTime(
        nullable=True,
    )

    status = ormar.Enum(
        enum_class=TaskStatuses,
        default=TaskStatuses.WAITING,
        nullable=False,
    )

metadata.create_all(bind=engine)
