import abc
import asyncio
import typing
from collections.abc import Callable
import re

import flet as ft
import pydantic
import datetime

import pydantic_core
from pydantic._internal._model_construction import ModelMetaclass
from pydantic.fields import FieldInfo
import settings

type ChoiceCallback = typing.Callable[[typing.Any], tuple[str, typing.Any]]
type ChoicesType = tuple[list[typing.Any], ChoiceCallback]

class BaseField[T:str](ft.UserControl):
    def __init__(self,
                 field: FieldInfo,
                 required: bool = None,
                 choices: ChoicesType = None,
                 value: T = None,
                 max_length: int = None,
                 on_change: typing.Callable[[ft.ControlEvent, T], typing.Any] = None,
                 error_text: str = None,
                 **kwargs
                 ):
        super().__init__(**kwargs)
        self._required = required or False
        self._field_info = field
        self._choices = choices
        self._max_length = max_length
        self.value = value
        self._error_text = error_text
        self._on_change_callback = on_change
        self.data = {
            'required': self._required,
        }

        self.field_ref = ft.Ref()

    @staticmethod
    @abc.abstractmethod
    def check_compatibility(field: FieldInfo) -> bool:
        raise NotImplemented(
            "Переопределите данный метод для проверки типа"
        )

    @abc.abstractmethod
    def build(self) -> ft.Control:
        raise NotImplemented(
            "Переопределите данный метод для отображения данных"
        )

    def handle_change(self, event: ft.ControlEvent):
        self.value = event.control.value
        self._on_change_callback and self._on_change_callback(event, event.control.value)

    @property
    def error_text(self):
        return self._error_text

    @error_text.setter
    def error_text(self, value: str):
        self._error_text = value
        if self.field_ref.current:
            self.field_ref.current.error_text = value
        self.update()

class StringField(BaseField[str]):
    @staticmethod
    def check_compatibility(field: FieldInfo) -> bool:
        return field.annotation == str

    def build(self):
        return ft.TextField(
            ref=self.field_ref,
            label=self._field_info.title,
            suffix_text='*' if self._required else None,
            suffix_style=ft.TextStyle(color='red'),
            value=self.value or '',
            tooltip=self._field_info.description,
            keyboard_type=ft.KeyboardType.TEXT,
            on_change=self.handle_change,
            password=False,
            can_reveal_password=False,
            # input_filter=ft.InputFilter(
            #     regex_string=r"^\+7(\s|-)?(\()?[0-9]{3}(\)) (\s)?([0-9]{3})-?([0-9]{2})-?([0-9]{2})$",
            #     allow=True,
            # ),
            data={
                'required': self._required
            }
        )

class DateField(BaseField[str]):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.day_ref = ft.Ref()
        self.month_ref = ft.Ref()
        self.year_ref = ft.Ref()

        self.validated = {
            'day': False,
            'month': False,
            'year': False,
        }

    @staticmethod
    def check_compatibility(field: FieldInfo) -> bool:
        return field.annotation in [
            datetime.date,
            datetime.datetime,
        ]


    def build(self):
        return ft.Column(
            controls=[
                ft.Text(value=self._field_info.title),
                ft.Row(
                    spacing=5,
                    controls=[
                        ft.TextField(
                            width=85,
                            hint_text="День",
                            ref=self.day_ref,
                            on_change=self.handle_day_change,
                            suffix_text="*",
                            suffix_style=ft.TextStyle(color='red'),
                            max_length=2,
                            max_lines=1,
                            data={
                                'step': 1,
                            }
                        ),
                        ft.TextField(
                            width=85,
                            hint_text="Месяц",
                            ref=self.month_ref,
                            on_change=self.handle_month_change,
                            suffix_text="*",
                            suffix_style=ft.TextStyle(color='red'),
                            max_length=2,
                            max_lines=1,
                            data={
                                'step': 2,
                            }
                        ),
                        ft.TextField(
                            width=120,
                            hint_text="Год",
                            ref=self.year_ref,
                            on_change=self.handle_year_change,
                            suffix_text="*",
                            suffix_style=ft.TextStyle(color='red'),
                            max_length=4,
                            max_lines=1,
                            data={
                                'step': 3,
                            }
                        )
                    ]
                )
            ]
        )

    def handle_day_change(self, event: ft.ControlEvent):
        day = int(self.day_ref.current.value) if self.day_ref.current.value.isdigit() else 0
        if day > 31:
            self.day_ref.current.error_text = '> 31'
        elif day < 1:
            self.day_ref.current.error_text = '< 1'
        elif len(self.day_ref.current.value) == self.day_ref.current.max_length:
            self.month_ref.current.focus()
            self.validated['day'] = True
        self.update()
        self.handle_change(event)

    def handle_month_change(self, event: ft.ControlEvent):
        month = int(self.month_ref.current.value) if self.month_ref.current.value.isdigit() else 0
        if month > 12:
            self.month_ref.current.error_text = '> 12'
        elif month < 1:
            self.month_ref.current.error_text = '< 1'
        elif len(self.month_ref.current.value) == self.month_ref.current.max_length:
            self.validated['month'] = True
            self.year_ref.current.focus()
        self.update()
        self.handle_change(event)

    def handle_year_change(self, event: ft.ControlEvent):
        year = int(self.year_ref.current.value) if self.year_ref.current.value.isdigit() else 0
        if year > 2100:
            self.year_ref.current.error_text = '> 2100'
        elif year < 1920:
            self.year_ref.current.error_text = '< 1920'
        else:
            self.validated['year'] = True
        self.update()
        self.handle_change(event)


    def handle_change(self, event: ft.ControlEvent):
        year, month, day = (
            int(self.year_ref.current.value) if self.year_ref.current.value.isdigit() else 0,
            int(self.day_ref.current.value) if self.day_ref.current.value.isdigit() else 0,
            int(self.day_ref.current.value) if self.day_ref.current.value.isdigit() else 0,
        )

        if not all([
            year,
            month,
            day
        ]) or not all([value for value in self.validated.values()]):
            self.year_ref.current.error_text = '!'
            self.month_ref.current.error_text = '!'
            self.day_ref.current.error_text = '!'
            return None

        value = str(
            datetime.date(
                year=int(self.year_ref.current.value),
                day=int(self.day_ref.current.value),
                month=int(self.month_ref.current.value),
            )
        ) + "T00:00"

        self.year_ref.current.error_text = None
        self.month_ref.current.error_text = None
        self.day_ref.current.error_text = None

        self.value = value
        self.update()
        self._on_change_callback and self._on_change_callback(event, value)

class ChoiceField(BaseField[str]):
    def build(self) -> ft.Control:
        return ft.Dropdown(
            ref=self.field_ref,
            suffix_text="*" if self._required else None,
            suffix_style=ft.TextStyle(color='red'),
            label=self._field_info.title,
            value=self.value,
            tooltip=self._field_info.description,
            on_change=self.handle_change,
            data={
                'required': self._required
            },
            options=[
                ft.dropdown.Option(
                    key=self._choices[1](option)[0], text=self._choices[1](option)[1],
                ) for option in self._choices[0]
            ] if self._choices else []
        )

    @staticmethod
    def check_compatibility(field: FieldInfo) -> bool:
        return False


class NumberField(BaseField[int]):
    @staticmethod
    def check_compatibility(field: FieldInfo) -> bool:
        return field.annotation == int

    def build(self):
        return ft.TextField(
            ref=self.field_ref,
            label=self._field_info.title,
            suffix_text='*' if self._required else None,
            suffix_style=ft.TextStyle(color='red'),
            value=str(self.value or 0),
            tooltip=self._field_info.description,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self.handle_change,
            password=False,
            can_reveal_password=False,
            max_length=self._max_length,
            max_lines=1,
            data={
                'required': self._required
            }
        )

    def handle_change(self, event: ft.ControlEvent):
        value = re.findall(r'\d+', event.control.value or "")
        if not value:
            value = 0
        else:
            value = int(value[0])
        self.value = value
        event.control.value = value
        self.update()
        self._on_change_callback and self._on_change_callback(event, value)


class BooleanField(BaseField[bool]):
    @staticmethod
    def check_compatibility(field: FieldInfo) -> bool:
        return field.annotation == bool


    def build(self) -> ft.Control:
        return ft.Switch(
            label=self._field_info.title,
            data={
                'required': self._required,
            },
            value=self.value,
            on_change=self.handle_change,
            tooltip=self.tooltip,
        )

class MaskedField(BaseField[str]):
    def __init__(self, mask: str, **kwargs):
        super().__init__(**kwargs)
        self._mask = mask
        self._masked_value = ""

    @staticmethod
    def check_compatibility(field: FieldInfo) -> bool:
        return False

    def build(self):
        return ft.TextField(
            ref=self.field_ref,
            label=self._field_info.title,
            suffix_text='*' if self._required else None,
            suffix_style=ft.TextStyle(color='red'),
            value=self.value or '',
            tooltip=self._field_info.description,
            keyboard_type=ft.KeyboardType.TEXT,
            on_change=self.handle_change,
            on_blur=self.handle_blur,
            on_focus=self.handle_focus,
            password=False,
            can_reveal_password=False,
            data={
                'required': self._required
            }
        )

    def apply_mask(self, value: str) -> tuple[str, str]:
        masked_number = ""
        number_index = 0

        for mask_char_index, char in enumerate(self._mask):
            if number_index > len(value) - 1:
                break
            elif char == 'x':  # Если это 'x', заменяем символом из номера
                masked_number += value[number_index]
                number_index += 1
            else:  # Иначе просто добавляем символ маски
                masked_number += char

        return masked_number, value[0:number_index]

    def handle_change(self, event: ft.ControlEvent):
        masked_value, raw_value = self.apply_mask(event.control.value)
        self._masked_value = masked_value
        self.value = raw_value
        self._on_change_callback and self._on_change_callback(event, raw_value)

    def handle_blur(self, event: ft.ControlEvent):
        self.field_ref.current.value = self._masked_value
        self.update()

    def handle_focus(self, event: ft.ControlEvent):
        self.field_ref.current.value = self.value
        self.update()

class PasswordField(BaseField[str]):
    @staticmethod
    def check_compatibility(field: FieldInfo) -> bool:
        return False

    def build(self) -> ft.Control:
        return ft.TextField(
            label=self._field_info.title,
            suffix_text='*' if self._required else None,
            suffix_style=ft.TextStyle(color='red'),
            value=self.value,
            tooltip=self._field_info.description,
            keyboard_type=ft.KeyboardType.VISIBLE_PASSWORD,
            on_change=self.handle_change,
            password=True,
            can_reveal_password=True,
            data={
                'required': self._required
            }
        )

class FletForm(ft.UserControl):
    """
    Виджет формы, адаптирующийся почти под любую модель pydantic.
    """

    def __init__(
            self,
            model: type[pydantic.BaseModel],
            handle_form_submit: typing.Callable[[dict], typing.Any] = None,
            submit_button_text: str = 'Ввести',
            actions: list[ft.Control] = None,
            choices: dict[str, ChoicesType] = None,
            initial_values: dict = None,
            masks: dict[str, dict[str] | str] = None,
            **kwargs
    ):

        self.__model = model
        self.__handle_form_submit = handle_form_submit
        self.__submit_button_text = submit_button_text
        self.__actions = actions
        self.__choices = choices

        self.__values = {}
        self.__fields = {}
        self.__initial_values = initial_values or {}
        self.__masks = masks or {}

        self.__subform_validated = {}
        self.__subform_button_refs = {}

        super().__init__(**kwargs)

    @staticmethod
    def get_field_control(field: pydantic.fields.FieldInfo) -> type[BaseField] | None:
        fields_filtered = list(
            filter(
                lambda klass, f=field: klass.check_compatibility(f),
                BaseField.__subclasses__()
            )
        )
        if not fields_filtered:
            return None

        return fields_filtered[-1]

    @staticmethod
    def get_error_for_field(errors: list, field_name: str):
        result = list(filter(
            lambda error: field_name in error['loc'],
            errors
        ))

        if not result:
            return None

        return result[0]

    def handle_field_errors(self, validation_error: pydantic.ValidationError, path: list[str] = None):
        errors = validation_error.errors()

        fields_controls = self.__fields if not path else self.get_attr_by_path(path, self.__fields)
        for field_name, field in fields_controls.items():
            if isinstance(field, dict):
                self.handle_field_errors(validation_error, [*(path or []), field_name])
                continue

            if not field.value and field.data.get('required'):
                field.error_text = 'Данное поле обязательно для заполнения.'
                continue

            error = self.get_error_for_field(errors, field_name)
            if not error:
                continue

            error_message = error.get('ctx', {}).get('error', None) or error.get('msg')
            if not error_message:
                continue

            message = str(error_message)
            field.error_text = message

        self.update()
        self.page.update()

    def clear_field_errors(self, fields: dict = None):
        fields = self.__fields if not fields else fields
        for _, field in fields.items():
            if isinstance(field, dict):
                self.clear_field_errors(field)
            else:
                field.error_text = None

        self.page.update()

    @staticmethod
    def set_attr_by_path[T:dict](path: list, data: T, value: typing.Any) -> T:
        prev_data = data
        last_index = len(path) - 1

        for index, line in enumerate(path):
            if not line:
                continue

            if not prev_data.get(line):
                prev_data[line] = {}

            if index == last_index:
                prev_data[line] = value
                break

            prev_data = prev_data.get(line)

        return data

    def handle_field_change(self, event: ft.ControlEvent, value: typing.Any, field_path: list):
        self.set_attr_by_path(
            field_path,
            self.__values,
            value,
        )

        if hasattr(event.control, 'error_text') and event.control.error_text:
            event.control.error_text = ''
            event.control.update()
            self.update()
            self.page.update()

    def handle_subform_submit(self, path: list[str], on_close: Callable[[], typing.Any]):
        model = self.get_attr_by_path(path, self.__model)
        values = self.get_attr_by_path(path, self.__values).copy()
        fields = self.get_attr_by_path(path, self.__fields).copy()
        self.set_attr_by_path(path, self.__subform_validated, False)
        button_ref = self.get_attr_by_path(path, self.__subform_button_refs)

        try:
            self.clear_field_errors(fields)
            model.model_validate(values)
            self.set_attr_by_path(path, self.__subform_validated, True)
            on_close()
            self.update()
        except pydantic.ValidationError as validation_error:
            self.set_attr_by_path(path, self.__subform_validated, False)
            self.handle_field_errors(validation_error, path=path)

        validated = self.get_attr_by_path(path, self.__subform_validated)
        button_ref.current.style.color = ft.colors.RED if not validated else ft.colors.GREEN
        self.page.update()
        self.update()

    def handle_form_submit(self, _):
        try:
            self.clear_field_errors()
            self.__model.model_validate(self.__values)

            if self.__handle_form_submit and not asyncio.iscoroutinefunction(self.__handle_form_submit):
                return self.__handle_form_submit(self.__values.copy())
            elif asyncio.iscoroutinefunction(self.__handle_form_submit):
                return settings.LOOP.run_until_complete(self.__handle_form_submit(self.__values.copy()))

        except pydantic.ValidationError as validation_error:
            self.handle_field_errors(validation_error)

    def get_attr_by_path(self, path: list, data: typing.Any):
        if not path:
            return None

        path_list = path.copy()
        path_line = path_list.pop(-1)

        if isinstance(data, dict):
            output = data.get(path_line, None)
        elif isinstance(data, ModelMetaclass):
            output = data.__dict__['__annotations__'].get(path_line, None)
        else:
            output = getattr(data, path_line, None)

        if not path_list:
            return output

        return self.get_attr_by_path(path_list, output)

    def handle_dialog_close(self, *_):
        self.page.close_dialog()
        self.page.update()

    def handle_open_alert_form_dialog(self, field: pydantic.fields.FieldInfo, path: list[str], form_content: ft.Control):
        def handle_dialog_close(*_):
            validated = self.get_attr_by_path(path, self.__subform_validated)
            button_ref = self.get_attr_by_path(path, self.__subform_button_refs)
            button_ref.current.style.color = ft.colors.RED if not validated else ft.colors.GREEN
            self.page.close(dialog)
            self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text(
                value=field.title
            ),
            modal=True,
            scrollable=True,
            content_padding=ft.Padding(top=20, bottom=20, left=20, right=20),
            content=ft.Container(
                width=315,
                content=form_content,
                alignment=ft.alignment.center,
            ),
            actions=[
                ft.FilledButton(
                    text="Сохранить",
                    on_click=lambda *_, p=path, on_close=handle_dialog_close: self.handle_subform_submit(path=p, on_close=on_close),
                ),
                ft.OutlinedButton(
                    text="Отмена",
                    style=ft.ButtonStyle(
                        color=ft.colors.RED,
                    ),
                    on_click=lambda *_, on_close=handle_dialog_close: on_close(),
                )
            ]
        )

        self.page.open(dialog)
        self.page.update()

    def get_field_initial_value(self, field: FieldInfo, field_path: list[str], values: dict = None):
        initial_value = self.get_attr_by_path(
            field_path,
            self.__initial_values,
        )

        if initial_value:
            self.set_attr_by_path(field_path, values, initial_value)
            return initial_value

        default_value = field.get_default(call_default_factory=True)
        self.set_attr_by_path(
            field_path,
            values,
            default_value if not isinstance(default_value, pydantic_core.PydanticUndefinedType) else ''
        )

        return self.get_attr_by_path(field_path, values)

    def _build_fields(self, path: list = None):
        fields_list = self.__model.__fields__ if not path else self.get_attr_by_path(path, self.__model).__fields__
        container = ft.Column(scroll=ft.ScrollMode.ADAPTIVE)
        values = {}
        fields = {}

        for field_name, field in fields_list.items():
            field_path = (path or []) + [field_name]
            if type(field.annotation) == ModelMetaclass:
                model_fields, model_values, model_container = self._build_fields(
                   field_path,
                )

                values.update(model_values)
                fields[field_name] = model_fields

                subfield_validated = self.get_attr_by_path(
                    field_path,
                    self.__subform_validated,
                )

                ref = ft.Ref()
                self.set_attr_by_path(field_path, self.__subform_button_refs, ref)

                container.horizontal_alignment = ft.CrossAxisAlignment.CENTER
                container.controls.append(
                    ft.OutlinedButton(
                        ref=ref,
                        text=field.title,
                        width=300,
                        height=50,
                        style=ft.ButtonStyle(
                            color=ft.colors.RED if not subfield_validated else ft.colors.GREEN,
                            shape=ft.RoundedRectangleBorder(radius=5),
                            side=ft.BorderSide(1, ft.colors.BLACK)
                        ),
                        on_click=lambda *_, content=model_container, f=field, path=field_path: self.handle_open_alert_form_dialog(f, path, content)
                    )
                )
                continue

            is_required = field.is_required()
            choices = None if not self.__choices else self.__choices.get(field_name, None)
            mask = self.get_attr_by_path(field_path, self.__masks)
            initial_value = self.get_field_initial_value(field, field_path, values)

            if mask:
                container.controls.append(
                    ft.Row([
                        field_control := MaskedField(
                            value=initial_value,
                            field=field,
                            required=is_required,
                            on_change=lambda event, value, fp=field_path: self.handle_field_change(event, value, fp),
                            mask=mask,
                        ),
                    ])
                )
            elif choices:
                container.controls.append(
                    ft.Row([
                        field_control := ChoiceField(
                            value=initial_value,
                            field=field,
                            required=is_required,
                            choices=choices,
                            on_change=lambda event, value, fp=field_path: self.handle_field_change(event, value, fp)
                        )
                    ])
                )
            else:
                field_class = self.get_field_control(field)
                if not field_class:
                    continue

                container.controls.append(
                    ft.Row([
                        field_control := field_class(
                            field=field,
                            value=initial_value,
                            required=is_required,
                            on_change=lambda event, value, fp=field_path: self.handle_field_change(event, value, fp)
                        )
                    ])
                )

            fields[field_name] = field_control

        return fields, values, container

    def build(self):
        fields, values, container = self._build_fields()

        self.__values = values.copy()
        self.__fields = fields.copy()

        if not self.__actions:
            self.__actions = []

        actions = ft.Row(
            controls=[
                ft.ElevatedButton(
                    text=self.__submit_button_text,
                    on_click=self.handle_form_submit
                ),
                *self.__actions
            ],
            alignment=ft.MainAxisAlignment.CENTER
        )

        container.controls.append(actions)
        return container
