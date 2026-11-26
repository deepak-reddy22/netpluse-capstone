from datetime import timezone

import pytest

from app.models import DeviceCreate, DeviceStatus
from app.repositories.device_repository import InMemoryDeviceRepository
from app.services.device_service import (
    DeviceAlreadyExistsError,
    DeviceNotFoundError,
    DeviceService,
)


@pytest.fixture
def repository() -> InMemoryDeviceRepository:
    return InMemoryDeviceRepository()


@pytest.fixture
def service(repository: InMemoryDeviceRepository) -> DeviceService:
    return DeviceService(repository)


def make_device(
    device_id: str = "RTR-101", status: DeviceStatus = DeviceStatus.online
) -> DeviceCreate:
    return DeviceCreate(
        device_id=device_id,
        name="Branch Router",
        device_type="router",
        ip_address="192.168.10.1",
        status=status,
    )


def test_register_device(service: DeviceService) -> None:
    device = service.register(make_device())

    assert device.device_id == "RTR-101"
    assert device.status == DeviceStatus.online
    assert service.list() == [device]


def test_duplicate_registration_raises_error(service: DeviceService) -> None:
    service.register(make_device())

    with pytest.raises(DeviceAlreadyExistsError):
        service.register(make_device())


def test_missing_device_raises_error(service: DeviceService) -> None:
    with pytest.raises(DeviceNotFoundError):
        service.get("missing")

    with pytest.raises(DeviceNotFoundError):
        service.update_status("missing", DeviceStatus.offline)


def test_initial_offline_registration_does_not_create_alert(
    service: DeviceService, repository: InMemoryDeviceRepository
) -> None:
    service.register(make_device(status=DeviceStatus.offline))

    assert repository.list_alerts() == []


def test_online_to_offline_creates_one_alert(
    service: DeviceService, repository: InMemoryDeviceRepository
) -> None:
    service.register(make_device())

    device = service.update_status("RTR-101", DeviceStatus.offline)
    alerts = repository.list_alerts()

    assert device.status == DeviceStatus.offline
    assert len(alerts) == 1
    assert alerts[0].device_id == "RTR-101"
    assert "went offline" in alerts[0].message
    assert alerts[0].timestamp.tzinfo == timezone.utc


def test_repeated_offline_update_does_not_create_another_alert(
    service: DeviceService, repository: InMemoryDeviceRepository
) -> None:
    service.register(make_device())
    service.update_status("RTR-101", DeviceStatus.offline)
    service.update_status("RTR-101", DeviceStatus.offline)

    assert len(repository.list_alerts()) == 1
