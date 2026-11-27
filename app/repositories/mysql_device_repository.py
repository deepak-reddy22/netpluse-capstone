from datetime import timezone
from sqlite3 import SQLITE_CONSTRAINT_PRIMARYKEY

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Alert, Device
from app.models import AlertResponse, DeviceResponse, DeviceStatus
from app.services.device_service import DeviceAlreadyExistsError


class MySqlDeviceRepository:
    def __init__(self, session: Session, *, lock_devices: bool = False) -> None:
        self.session = session
        self.lock_devices = lock_devices

    def add_device(self, device: DeviceResponse) -> DeviceResponse:
        self.session.add(Device(**device.model_dump(mode="json")))
        try:
            self.session.flush()
        except IntegrityError as exc:
            if exc.orig.args[:1] == (1062,) or getattr(
                exc.orig, "sqlite_errorcode", None
            ) == SQLITE_CONSTRAINT_PRIMARYKEY:
                raise DeviceAlreadyExistsError(device.device_id) from exc
            raise
        return device.model_copy(deep=True)

    def list_devices(self) -> list[DeviceResponse]:
        return [
            DeviceResponse.model_validate(row, from_attributes=True)
            for row in self.session.scalars(select(Device).order_by(Device.device_id))
        ]

    def get_device(self, device_id: str) -> DeviceResponse | None:
        row = self.session.get(Device, device_id, with_for_update=self.lock_devices)
        return DeviceResponse.model_validate(row, from_attributes=True) if row else None

    def update_status(self, device_id: str, status: DeviceStatus) -> DeviceResponse | None:
        row = self.session.get(Device, device_id)
        if row is None:
            return None
        row.status = status.value
        self.session.flush()
        return DeviceResponse.model_validate(row, from_attributes=True)

    def save_alert(self, alert: AlertResponse) -> AlertResponse:
        self.session.add(Alert(
            device_id=alert.device_id, message=alert.message,
            timestamp=alert.timestamp.astimezone(timezone.utc).replace(tzinfo=None),
        ))
        self.session.flush()
        return alert.model_copy(deep=True)

    def list_alerts(self) -> list[AlertResponse]:
        return [
            AlertResponse(device_id=row.device_id, message=row.message,
                          timestamp=row.timestamp.replace(tzinfo=timezone.utc))
            for row in self.session.scalars(select(Alert).order_by(Alert.id))
        ]
