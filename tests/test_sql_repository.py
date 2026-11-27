import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import DeviceCreate, DeviceStatus
from app.repositories.mysql_device_repository import MySqlDeviceRepository
from app.services.device_service import DeviceAlreadyExistsError, DeviceService


@pytest.fixture
def sessions(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'netpulse.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    command.upgrade(Config("alembic.ini"), "head")
    engine = create_engine(url)
    try:
        yield sessionmaker(engine)
    finally:
        engine.dispose()


def test_transitions_persist_across_sessions(sessions):
    device = DeviceCreate.model_validate({
        "device_id": "RTR-101", "name": "Branch Router",
        "device_type": "router", "ip_address": "192.168.10.1",
    })
    with sessions.begin() as db:
        registered = DeviceService(MySqlDeviceRepository(db)).register(device)
    for _ in range(2):
        with sessions.begin() as db:
            DeviceService(MySqlDeviceRepository(db)).update_status(device.device_id, DeviceStatus.offline)
    with sessions.begin() as db:
        repo = MySqlDeviceRepository(db)
        assert repo.list_devices() == [registered.model_copy(update={"status": DeviceStatus.offline})]
        alerts = repo.list_alerts()
        assert [alert.device_id for alert in alerts] == [device.device_id]
        assert alerts[0].timestamp.tzinfo is not None
    with pytest.raises(DeviceAlreadyExistsError), sessions.begin() as db:
        DeviceService(MySqlDeviceRepository(db)).register(device)
    with pytest.raises(DeviceAlreadyExistsError), sessions.begin() as db:
        MySqlDeviceRepository(db).add_device(registered)
