# NetPulse

NetPulse is a small FastAPI modular monolith for registering network devices and
recording an alert when a device changes from online to offline. It simulates
monitoring state only; it does not ping devices. By default, data live in memory
and are cleared on restart. Select MySQL for persistent devices and alerts.

## Quick start (no database required)

Open the project folder in VS Code and select **Terminal > New Terminal**.
On Linux or macOS, run these commands once from the folder containing
`requirements.txt`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows PowerShell, use `py -m venv .venv` and `.\.venv\Scripts\Activate.ps1`
for the first two commands. Once the environment is active, start the API:

```bash
python -m uvicorn app.main:app --reload
```

Open the [health check](http://127.0.0.1:8000/health). If the server is running,
you'll see `{"status":"ok"}`. To send requests from your browser, open
[Swagger UI](http://127.0.0.1:8000/docs), expand an endpoint, and select
**Try it out**. FastAPI generates the [OpenAPI schema](http://127.0.0.1:8000/openapi.json)
from the routes and models.

Keep the terminal open while using the API. Press **Ctrl+C** to stop it.
Next time, activate the existing environment and run the start command again.

## API reference

| Method | Path | Result |
| --- | --- | --- |
| POST | `/devices` | Register a device (`201`; `409` if its ID already exists). |
| GET | `/devices` | List registered devices. |
| GET | `/devices/{device_id}` | Get one device (`404` if not found). |
| PATCH | `/devices/{device_id}/status` | Update the device status (`404` if not found). |
| GET | `/alerts` | List recorded offline alerts. |
| GET | `/health` | Check that the API is responding. |

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
