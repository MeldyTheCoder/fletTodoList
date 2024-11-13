import typing
from ctypes.wintypes import tagRECT

import flet as ft

import models

TITLE_FONT_STYLE = ft.TextStyle(
    weight=ft.FontWeight.W_600,
    size=18,
)

STATUS_FONT_STYLE = ft.TextStyle(
    weight=ft.FontWeight.W_500,
    size=14,
)

class TodoList(ft.UserControl):
    def __init__(self,
            tasks: list[models.Task],
            on_task_delete: typing.Callable[[models.Task], typing.Any] = None,
            on_task_group_switch: typing.Callable[[models.Task, models.TaskStatuses], typing.Any] = None,
            on_task_edit: typing.Callable[[models.Task], typing.Any] = None,
            **kwargs
        ):
        super().__init__(**kwargs)

        self._tasks = tasks
        self._selected_ids = ft.Ref()
        self._selected_ids.current = []

        self._on_task_delete = on_task_delete
        self._on_task_group_switch = on_task_group_switch
        self._on_task_edit = on_task_edit

        self.listview = ft.ListView(
            width=self.width,
            height=self.height,
            spacing=10,
        )

    @staticmethod
    def get_bg_by_priority(status: models.TaskStatuses):
        if status == models.TaskStatuses.WAITING:
            return ft.colors.GREY_50, ft.colors.BLACK
        elif status == models.TaskStatuses.REMOVED:
            return ft.colors.RED, ft.colors.WHITE
        elif status == models.TaskStatuses.COMPLETED:
            return ft.colors.GREEN, ft.colors.WHITE

    def handle_task_click(self, event: ft.ControlEvent, task: models.Task):
        if task.id not in self._selected_ids.current:
            self._selected_ids.current.append(task.id)
            event.control.selected = True
        else:
            self._selected_ids.current.remove(task.id)
            event.control.selected = False
        self.update()

    def handle_task_edit_mode(self, task: models.Task):
        if self._on_task_edit:
            self._on_task_edit(task)

    @property
    def tasks(self):
        return self.listview.controls

    @tasks.setter
    def tasks(self, value: list[models.Task]):
        value = sorted(value.copy(), key=lambda record: record.priority, reverse=True)

        self.listview.controls = [
            ft.ListTile(
                key=task.id,
                style=ft.ListTileStyle.LIST,
                text_color=self.get_bg_by_priority(task.status)[1],
                bgcolor=self.get_bg_by_priority(task.status)[0],
                bgcolor_activated=self.get_bg_by_priority(task.status)[0],
                title=ft.Text(value=task.task, style=TITLE_FONT_STYLE),
                selected=False,
                enable_feedback=False,
                subtitle=self.get_status_control(task.status),
                tooltip=task.task,
                on_click=lambda event, t=task: self.handle_task_click(event, t),
                leading=ft.Text(value=task.priority),
                trailing=ft.PopupMenuButton(
                    icon=ft.icons.MORE_VERT,
                    items=[
                        ft.PopupMenuItem(
                            text="Редактировать",
                            on_click=lambda *_, t=task: self.handle_task_edit_mode(t),
                        ),
                        ft.PopupMenuItem(
                            text="Удалить",
                            on_click=lambda *_, t=task: self.handle_task_delete(t),
                        ),
                        ft.PopupMenuItem(
                            text="В прогрессе",
                            on_click=lambda *_, t=task: self.handle_task_group_switch(t,
                                                                                      models.TaskStatuses.WAITING),
                        ),
                        ft.PopupMenuItem(
                            text="Завершено",
                            on_click=lambda *_, t=task: self.handle_task_group_switch(t,
                                                                                      models.TaskStatuses.COMPLETED),
                        ),
                        ft.PopupMenuItem(
                            text="Отменено",
                            on_click=lambda *_, t=task: self.handle_task_group_switch(t,
                                                                                      models.TaskStatuses.REMOVED),
                        )
                    ]
                )
            ) for task in value
        ]

    @staticmethod
    def get_status_control(status: models.TaskStatuses):
        row_props = dict(
            spacing=2,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        icon_props = {
            'size': 14,
        }

        if status == models.TaskStatuses.WAITING:
            return ft.Row(
                **row_props,
                controls=[
                    ft.Icon(
                        ft.icons.WATCH,
                        **icon_props,
                    ),
                    ft.Text(
                        value=status.value,
                        style=STATUS_FONT_STYLE,
                    )
                ]
            )
        elif status == models.TaskStatuses.REMOVED:
            return ft.Row(
                **row_props,
                controls=[
                    ft.Icon(
                        ft.icons.REMOVE,
                        **icon_props,
                    ),
                    ft.Text(
                        value=status.value,
                        style=STATUS_FONT_STYLE,
                    )
                ]
            )

        elif status == models.TaskStatuses.COMPLETED:
            return ft.Row(
                **row_props,
                controls=[
                    ft.Icon(
                        ft.icons.CHECK,
                        **icon_props,
                    ),
                    ft.Text(
                        value=status.value,
                        style=STATUS_FONT_STYLE,
                    )
                ]
            )

    def handle_task_delete(self, task: models.Task):
        self.listview.controls = list(
            filter(
                lambda control: int(control.key) != task.id,
                self.listview.controls,
            )
        )
        if self._on_task_delete:
            self._on_task_delete(task)
        self.update()

    def handle_task_group_switch(self, task: models.Task, status: models.TaskStatuses):
        self.listview.controls = list(
            filter(
                lambda control: int(control.key) != task.id,
                self.listview.controls,
            )
        )
        if self._on_task_group_switch:
            self._on_task_group_switch(task, status)
        self.update()

    def build(self):
        self.tasks = self._tasks

        return self.listview