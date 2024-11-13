import flet as ft
import asyncio

import models
from components.flet_form import FletForm
from components.todo_list import TodoList
from serializers import TaskCreateSerializer

loop = asyncio.get_event_loop()

async def run_database_backend():
    if not models.database.is_connected:
        await models.database.connect()

def main(page: ft.Page):
    page.title = 'TODO-List'
    page.horizontal_alignment = ft.MainAxisAlignment.CENTER

    def get_toolbar_by_status(status: models.TaskStatuses):
        def handle_priority_change(event: ft.ControlEvent):
            value = int(event.control.value)

            query = models.Task.objects.filter(
                status=status,
            )
            if value > 0:
                query = query.filter(
                    priority=value
                )

            tasks_ = loop.run_until_complete(
                query.all()
            )
            todo_list = listview_dict[status]
            todo_list.tasks = tasks_
            todo_list.update()
            page.update()

        return ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
            controls=[
                ft.CupertinoButton(
                    text="Создать",
                    bgcolor=ft.colors.GREEN,
                    on_click=lambda *_, g=status: handle_open_create_dialog(g)
                ),
                ft.CupertinoButton(
                    text="Удалить",
                    bgcolor=ft.colors.RED,
                ),
                ft.Dropdown(
                    label="Приоритет",
                    on_change=handle_priority_change,
                    value="0",
                    options=[
                        ft.dropdown.Option(
                            key=f"{i}",
                            text=f"{i}",
                        ) for i in range(1, 6)
                    ] + [
                        ft.dropdown.Option(
                            key="0",
                            text="не выбрано"
                        ),
                    ]
                )
            ]
        )

    def handle_open_create_dialog(group: models.TaskStatuses):
        def handle_form_submit(value):
            handle_task_create(value, group)
            page.close(dialog)

        dialog = ft.AlertDialog(
            content=ft.Container(
                width=300,
                content=FletForm(
                    model=TaskCreateSerializer,
                    handle_form_submit=handle_form_submit,
                    submit_button_text="Создать",
                ),
            )
        )
        page.open(dialog)
        page.update()

    def handle_open_edit_dialog(task: models.Task):
        def handle_form_submit(value):
            loop.run_until_complete(
                task.update(**value)
            )
            tasks_ = loop.run_until_complete(
                models.Task.objects.filter(
                    status=task.status,
                ).all()
            )
            todo_list = listview_dict[task.status]
            todo_list.tasks = tasks_
            todo_list.update()
            page.close(dialog)

        dialog = ft.AlertDialog(
            content=ft.Container(
                width=300,
                content=FletForm(
                    initial_values=task.model_dump(include={'task', 'deadline', 'priority'}),
                    model=TaskCreateSerializer,
                    handle_form_submit=handle_form_submit,
                    submit_button_text="Редактировать",
                ),
            )
        )
        page.open(dialog)
        page.update()

    def handle_task_create(data: dict, group: models.TaskStatuses):
        loop.run_until_complete(
            models.Task.objects.create(
                task=data['task'],
                deadline=data['deadline'],
                priority=data['priority'],
                status=group,
            )
        )

        tasks_ = loop.run_until_complete(
            models.Task.objects.filter(
                status=group,
            ).all()
        )

        todo_list = listview_dict[group]
        todo_list.tasks = tasks_
        todo_list.update()
        page.update()

    def handle_group_change(task: models.Task, status: models.TaskStatuses):
        loop.run_until_complete(
            task.update(
                status=status
            )
        )

        tasks_ = loop.run_until_complete(
            models.Task.objects.filter(
                status=status,
            ).all()
        )

        todo_list: TodoList = listview_dict[status]
        todo_list.tasks = tasks_
        todo_list.update()
        page.update()

    def handle_task_delete(task: models.Task):
        loop.run_until_complete(
            task.delete()
        )

        tasks_ = loop.run_until_complete(
            models.Task.objects.filter(
                status=task.status,
            ).all()
        )

        todo_list: TodoList = listview_dict[task.status]
        todo_list.tasks = tasks_
        todo_list.update()
        page.update()

    loop.run_until_complete(
        run_database_backend()
    )

    waiting_tasks = loop.run_until_complete(
        models.Task.objects.filter(
            status=models.TaskStatuses.WAITING,
        ).all()
    )

    removed_tasks = loop.run_until_complete(
        models.Task.objects.filter(
            status=models.TaskStatuses.REMOVED,
        ).all()
    )

    completed_tasks = loop.run_until_complete(
        models.Task.objects.filter(
            status=models.TaskStatuses.COMPLETED,
        ).all()
    )

    waiting_todo_list = TodoList(
        tasks=waiting_tasks,
        height=500,
        width=700,
        on_task_delete=handle_task_delete,
        on_task_group_switch=handle_group_change,
        on_task_edit=handle_open_edit_dialog,
    )

    removed_todo_list = TodoList(
        tasks=removed_tasks,
        height=500,
        width=700,
        on_task_delete=handle_task_delete,
        on_task_group_switch=handle_group_change,
        on_task_edit=handle_open_edit_dialog,
    )

    completed_todo_list = TodoList(
        tasks=completed_tasks,
        height=500,
        width=700,
        on_task_delete=handle_task_delete,
        on_task_group_switch=handle_group_change,
        on_task_edit=handle_open_edit_dialog,
    )

    listview_dict = {
        models.TaskStatuses.WAITING: waiting_todo_list,
        models.TaskStatuses.COMPLETED: completed_todo_list,
        models.TaskStatuses.REMOVED: removed_todo_list,
    }

    page.add(
        ft.Tabs(
            height=500,
            tab_alignment=ft.TabAlignment.CENTER,
            tabs=[
                ft.Tab(
                    text="В прогрессе",
                    content=ft.Container(
                        ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                get_toolbar_by_status(models.TaskStatuses.WAITING),
                                waiting_todo_list,
                            ]
                        ),
                        padding=ft.Padding(
                            top=30,
                            bottom=0,
                            left=0,
                            right=0,
                        ),
                        alignment=ft.alignment.top_center,
                    ),
                ),
                ft.Tab(
                    text="Завершенные",
                    content=ft.Container(
                        ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                get_toolbar_by_status(models.TaskStatuses.COMPLETED),
                                completed_todo_list,
                            ]
                        ),
                        padding=ft.Padding(
                            top=30,
                            bottom=0,
                            left=0,
                            right=0,
                        ),
                        alignment=ft.alignment.top_center,
                    ),
                ),
                ft.Tab(
                    text="Отмененные",
                    content=ft.Container(
                        ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                get_toolbar_by_status(models.TaskStatuses.REMOVED),
                                removed_todo_list,
                            ]
                        ),
                        padding=ft.Padding(
                            top=30,
                            bottom=0,
                            left=0,
                            right=0,
                        ),
                        alignment=ft.alignment.top_center,
                    ),
                )
            ]
        )
    )

if __name__ == '__main__':
    ft.app(main)