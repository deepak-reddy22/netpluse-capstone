# NetPulse

NetPulse is a small FastAPI modular monolith for registering network devices and
recording an alert when a device changes from online to offline. It simulates
monitoring state only; it does not ping devices. By default, data live in memory
and are cleared on restart. Select MySQL for persistent devices and alerts.

## Run locally

From the project root, create and activate a virtual environment, then install
the dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows, activate the environment with `.venv\Scripts\activate` instead.
Start the API with:

```bash
uvicorn app.main:app --reload
```

Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for the Swagger
UI. FastAPI builds `/openapi.json` from the route declarations, request/response
models, field validation and documented response codes.

## Try the offline alert flow

1. In `POST /devices`, register:

   ```json
   {
     "device_id": "RTR-101",
     "name": "Branch Router",
     "device_type": "router",
     "ip_address": "192.168.10.1",
     "status": "online"
   }
   ```

2. Call `PATCH /devices/RTR-101/status` with `{"status": "offline"}` twice.
3. Call `GET /alerts`. There should be exactly one alert for `RTR-101`.
4. Registering `RTR-101` again returns HTTP 409. Invalid IPv4 addresses or
   unsupported device types/statuses return HTTP 422.

## Architecture

- **Routes** (`app/routes/devices.py`) define the HTTP API and translate service
  errors into HTTP status codes.
- **Service** (`app/services/device_service.py`) owns device rules, including
  duplicate/missing-device handling and detecting online-to-offline transitions.
- **Repositories** implement a shared interface for reading and writing devices
  and alerts. The SQL repository returns API models, not ORM objects.
- **Events** (`app/events.py`) creates and records an offline alert through the
  repository interface.

The app is one deployable modular monolith: these layers are organized within
one application and process. The route dependencies select a repository without
changing the service's alert rule. In SQL mode each request uses one transaction,
so the status change and its alert commit or roll back together.

## Run with MySQL

1. Create a dedicated MySQL database (`netpulse_db`) and grant a dedicated
   account permission to manage tables and data in that database only.
2. Copy `.env.example` to `.env`. Set the host, port, database, username and
   password locally. Leave `NETPULSE_BACKEND=mysql`. Alternatively, set
   `DATABASE_URL` to a `mysql+pymysql://` connection URL.
3. From the project root with the virtual environment active, run:

   ```bash
   alembic upgrade head
   alembic current
   alembic history
   uvicorn app.main:app --reload
   ```

4. Try the offline alert flow above, restart Uvicorn, then check `GET /devices`
   and `GET /alerts` again. The rows should still be present.

The two included revisions create `devices` and `alerts`, then add nullable
`devices.location`. Do not regenerate them during setup. For a future model
change, run `alembic revision --autogenerate -m "describe change"` and review
the generated operations. On a **disposable lab database**, test the second
revision with `alembic downgrade -1`, then `alembic upgrade head`; downgrading
discards any values in the location column.

## Tests

Run the service tests and the SQL repository test from the project root.
The latter runs migrations on a temporary SQLite database, not your MySQL data:

```bash
python -m pytest -q
```
