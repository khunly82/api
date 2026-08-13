import uuid
from typing import Annotated

from fastapi_cache import FastAPICache
import starlette.status
from fastapi import APIRouter, Body, Depends, File, HTTPException, Path, UploadFile
from PIL import Image
from sqlalchemy.exc import NoResultFound

from decorators.invalidate_cache_decorator import invalidate_cache
from dto.employee_request_dto import EmployeeRequestDto
from models.employee import Employee
from repositories.employee_repository import EmployeeRepository

router = APIRouter(prefix='/employees', tags=['Employees'])

@router.post('/', status_code=201)
def create(
    dto: Annotated[EmployeeRequestDto, Body()],
    employee_repository: Annotated[EmployeeRepository, Depends(EmployeeRepository)]
):
    try:
        sup = employee_repository.get_one(dto.supervisor_id)
    except NoResultFound:
        raise HTTPException(starlette.status.HTTP_422_UNPROCESSABLE_CONTENT)
    if sup.title == Employee.Title.DEV and dto.title == Employee.Title.PM:
        raise HTTPException(starlette.status.HTTP_422_UNPROCESSABLE_CONTENT)
    e = employee_repository.add(Employee(
        **dto.__dict__
    ))
    return e.id
        

@router.patch('/{id}/photo')
async def update_photo(
    id: Annotated[int, Path()],
    image: Annotated[UploadFile, File()],
    employee_repository: Annotated[EmployeeRepository, Depends(EmployeeRepository)]
):
    try:
        if image.size > 1024*1024*2:
            raise HTTPException(starlette.status.HTTP_422_UNPROCESSABLE_CONTENT)
        file = Image.open(image.file)
        filename = 'static/' + str(uuid.uuid4()) + '.webp'
        file.save(filename, 'WEBP', quality=85)
        e = employee_repository.update(id, photo=filename)
    except:
        raise HTTPException(starlette.status.HTTP_422_UNPROCESSABLE_CONTENT)
    return e  

@router.delete('/{id}')
@invalidate_cache(namespace='TASKS')
def delete(
    id: Annotated[int, Path()],
    employee_repository: Annotated[EmployeeRepository, Depends(EmployeeRepository)],
):
    try:
        employee = employee_repository.get_one(id)
    except NoResultFound:
        raise HTTPException(starlette.status.HTTP_404_NOT_FOUND)
    if not employee.supervisor_id:
        raise HTTPException(starlette.status.HTTP_422_UNPROCESSABLE_CONTENT)
    employee.supervisor.tasks.extend(employee.tasks)
    employee.supervisor.subordinates.extend(employee.subordinates)
    employee_repository.flush()

    return employee.id

@router.patch('/{id}/supervisor')
def update_supervisor(
    id: Annotated[int, Path()],
    employee_repository: Annotated[EmployeeRepository, Depends(EmployeeRepository)],
    supervisor_id: Annotated[int|None, Body()] = None,
):
    try:
        employee = employee_repository.get_one(id)
    except NoResultFound:
        raise HTTPException(starlette.status.HTTP_404_NOT_FOUND)
    if not supervisor_id:
        if employee.title == Employee.Title.DEV:
            raise HTTPException(starlette.status.HTTP_422_UNPROCESSABLE_CONTENT)
        employee_repository.update(id, supervisor=None)
    else:
        try:
            sup = employee_repository.get_one(supervisor_id)
            hierachy = employee_repository.get_hierarchy(supervisor_id)
            if employee in hierachy:
                raise HTTPException(starlette.status.HTTP_422_UNPROCESSABLE_CONTENT)
            employee_repository.update(id, supervisor=sup)
        except NoResultFound:
            raise HTTPException(starlette.status.HTTP_422_UNPROCESSABLE_CONTENT)
    return employee