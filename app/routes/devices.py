from fastapi import APIRouter, HTTPException, status

from app.models import AlertResponse, DeviceCreate, DeviceResponse, StatusUpdate
from app.dependencies import Repo, Service
from app.services.device_service import (
    DeviceAlreadyExistsError,
    DeviceNotFoundError,
)

router = APIRouter()


@router.post(
    "/devices",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"description": "A device with this ID already exists."}},
)
def register_device(device: DeviceCreate, service: Service) -> DeviceResponse:
    try:
        return service.register(device)
    except DeviceAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Device '{error}' already exists.",
        ) from error


@router.get("/devices", response_model=list[DeviceResponse])
def list_devices(service: Service) -> list[DeviceResponse]:
    return service.list()


@router.get(
    "/devices/{device_id}",
    response_model=DeviceResponse,
    responses={404: {"description": "Device not found."}},
)
def get_device(device_id: str, service: Service) -> DeviceResponse:
    try:
        return service.get(device_id)
    except DeviceNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device '{error}' was not found.",
        ) from error


@router.patch(
    "/devices/{device_id}/status",
    response_model=DeviceResponse,
    responses={404: {"description": "Device not found."}},
)
def update_device_status(device_id: str, update: StatusUpdate, service: Service) -> DeviceResponse:
    try:
        return service.update_status(device_id, update.status)
    except DeviceNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device '{error}' was not found.",
        ) from error


@router.get("/alerts", response_model=list[AlertResponse])
def list_alerts(repository: Repo) -> list[AlertResponse]:
    return repository.list_alerts()


@router.get("/health", response_model=dict[str, str])
def health() -> dict[str, str]:
    return {"status": "ok"}
