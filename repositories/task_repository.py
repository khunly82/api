from sqlalchemy import select
from sqlalchemy.orm import joinedload

from models.employee import Employee
from models.task import Task
from repositories.repository_base import RepositoryBase


class TaskRepository(RepositoryBase[Task]):
    model = Task

    def get_by_email_and_status(self, email: str, status: Task.Status, limit: int, page: int) -> list[Task]:
        stmt = (select(Task)
            .options(joinedload(Task.assign_to))
            # .join(Employee, isouter=True)
            .offset((page - 1) * limit)
            .limit(limit)
        )
        if email:
            stmt.join(Task.assign_to).where(Employee.email == email)
        if status:
            stmt.where(Task.status == status)

        tasks = self._session.execute(stmt).scalars().all()
        return list(tasks)
