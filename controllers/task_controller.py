from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Depends,
    HTTPException,
    Path,
    Query,
)
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache
from sqlalchemy.exc import NoResultFound
from starlette.status import *

from decorators.invalidate_cache_decorator import invalidate_cache
from dto.task_filter_request_dto import TaskFilterRequestDto
from dto.task_request_dto import TaskRequestDto
from dto.task_response_dto import TaskResponseDto
from models.employee import Employee
from models.task import Task
from repositories.employee_repository import EmployeeRepository
from repositories.task_repository import TaskRepository
from services.mailer import Mailer

router = APIRouter(prefix='/tasks', tags=['Tasks'])

@router.post('/', status_code=201)
@invalidate_cache(namespace='TASKS')
async def create(
    background_tasks: BackgroundTasks,
    dto: Annotated[TaskRequestDto, Body()],
    employee_repository: Annotated[EmployeeRepository, Depends(EmployeeRepository)],
    task_repository: Annotated[TaskRepository, Depends(TaskRepository)],
    mailer: Annotated[Mailer, Depends(Mailer)]
):
    empl = employee_repository.get_by_email(dto.attribution_email)
    if not empl:
        raise HTTPException(HTTP_422_UNPROCESSABLE_CONTENT, 'Employé introuvable')
    if empl.title != Employee.Title.DEV:
        raise HTTPException(HTTP_422_UNPROCESSABLE_CONTENT, 'On ne peut attribué de tâches qu\'aux dev')

    task = Task(
        name=dto.name,
        assign_to=empl,
        end_date=datetime.now(timezone.utc) + timedelta(days=dto.duration)
    )

    task_repository.add(task)

    print('----------------------------------------')
    print(task.__dict__)
    print('----------------------------------------')

    result: list[Employee] = employee_repository.get_hierarchy(empl.id)

    emails = [e.email for e in result]

    # envoyer l'email en arrière plan
    background_tasks.add_task(
        mailer.send_message,
        'Nouvelle tâche', 
        emails,
        task.__dict__,
        'new_task.html'
    )

    return { 'id':  task.id }

@router.get('/')
@cache(expire=300, namespace='TASKS')
def get(
    dto: Annotated[TaskFilterRequestDto, Query()],
    task_repository: Annotated[TaskRepository, Depends(TaskRepository)]
) -> list[TaskResponseDto]:

    tasks = task_repository.get_by_email_and_status(dto.email, dto.status, dto.limit, dto.page)
    
    # transforme chaque model db en dto
    return list(map(TaskResponseDto.from_entity, tasks))

@router.patch('/{id}')
@invalidate_cache(namespace='TASKS')
def update_status(
    id: Annotated[int, Path()], 
    status: Annotated[Task.Status, Body(...)],
    task_repository: Annotated[TaskRepository, Depends(TaskRepository)]
):
    try:
        task = task_repository.get_one(id)
    except NoResultFound:
        raise HTTPException(HTTP_404_NOT_FOUND)
    
    if task.end_date < datetime.now(timezone.utc):
        raise HTTPException(HTTP_422_UNPROCESSABLE_CONTENT, {
            'message': 'Il n\'est plus possible de modifier cet enregistrement'
        })

    task_repository.update(id, status=status)
    return task.id

@router.delete('/{id}')
@invalidate_cache(namespace='TASKS')
def delete(
    background_tasks: BackgroundTasks,
    id: Annotated[int, Path()], 
    task_repository: Annotated[TaskRepository, Depends(TaskRepository)],
    mailer: Annotated[Mailer, Depends(Mailer)]
):
    try:
        task = task_repository.get_one(id)
    except NoResultFound:
        raise HTTPException(HTTP_404_NOT_FOUND)

    if task.status == Task.Status.done:
        raise HTTPException(HTTP_422_UNPROCESSABLE_CONTENT, {
            'message': 'Impossible de supprimer une tâche terminée'
        })

    task_repository.delete(id)

    background_tasks.add_task(
        mailer.send_message,
        'Tâche supprimée',
        [task.attribution_email], # modifier ici 
        task.__dict__,
        'task_removed.html'
    )
    return task.id




    
