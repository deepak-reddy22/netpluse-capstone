from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.config import backend
from app.db.session import get_db
from app.repositories.device_repository import DeviceRepository, InMemoryDeviceRepository
from app.repositories.mysql_device_repository import MySqlDeviceRepository
from app.services.device_service import DeviceService


_memory = InMemoryDeviceRepository()


def memory_repository() -> DeviceRepository:
    return _memory


def sql_repository(request: Request, db: Annotated[Session, Depends(get_db, scope="function")]) -> DeviceRepository:
    return MySqlDeviceRepository(db, lock_devices=request.method == "PATCH")


Repo = Annotated[DeviceRepository, Depends(sql_repository if backend == "mysql" else memory_repository)]


def get_service(repository: Repo) -> DeviceService:
    return DeviceService(repository)


Service = Annotated[DeviceService, Depends(get_service)]
