from datetime import datetime

import pydantic


class Base(pydantic.BaseModel):
    pass


class TaskCreateSerializer(Base):
    task: str = pydantic.Field(
        title="Заголовок"
    )
    priority: int = pydantic.Field(
        title="Приоритет",
    )
    deadline: datetime = pydantic.Field(
        title="Дедлайн"
    )

    @pydantic.field_validator('task')
    def validate_task(cls, value: str):
        if 1 > len(value) > 80:
            raise ValueError(
                "Длина заголовка должна быть от 1 до 80 символов"
            )
        return value

    @pydantic.field_validator('priority')
    def validate_priority(cls, value: int):
        if 1 > value > 5:
            raise ValueError(
                "Значение приоритета должно быть от 1 до 5."
            )

        return value

