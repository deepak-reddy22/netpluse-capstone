# NetPulse

NetPulse is a small FastAPI modular monolith for registering network devices and
recording an alert when a device changes from online to offline. It simulates
monitoring state only; it does not ping devices or use a database. Device and
alert data live in memory and are cleared when the application restarts.

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
- **Repository** (`app/repositories/device_repository.py`) owns the in-memory
  dictionaries and alert list, returning copies to protect stored state.
- **Events** (`app/events.py`) creates and records an offline alert through the
  repository interface.

The app is one deployable modular monolith: these layers are organized within
one application and process. A future database-backed repository can replace
the in-memory repository while leaving service business rules unchanged.

## Tests

Run the isolated service tests from the project root:

```bash
python -m pytest -q
```
# netpluse-capstone
