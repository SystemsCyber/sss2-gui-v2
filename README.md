# SSS2 Control System

Smart Sensor Simulation 2 (SSS2) Control System with FastAPI backend and Svelte frontend.

## Project Structure

- `app-ui/` - FastAPI backend (serves API + built UI in production)
- `ui/` - Svelte frontend (built to static files)
- `scripts/` - Build scripts

## Quick Start

### Option 1: Development Mode (Frontend + Backend Separate)

**Terminal 1 - Backend:**
```bash
cd app-ui
pip install -r requirements.txt
python main.py
```

Backend runs on `http://localhost:8000`

**Terminal 2 - Frontend (Hot Reload):**
```bash
cd ui
npm install
npm run dev
```

Frontend runs on `http://localhost:5173` (Vite default) and proxies API calls to `http://localhost:8000`

### Option 2: Production Mode (Single Server)

**Build UI and copy to backend:**
```bash
./scripts/build-ui.sh
```

**Run backend (serves API + static UI):**
```bash
cd app-ui
pip install -r requirements.txt
python main.py
```

Or using uvicorn directly:
```bash
cd app-ui
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Access the application at `http://localhost:8000`

## Configuration

### Serial Port (Optional)

The serial port can be configured via environment variable:

```bash
export SSS2_SERIAL_PORT=/dev/tty.usbmodem40768801  # Mac default
# or
export SSS2_SERIAL_PORT=/dev/ttyACM0  # Linux/Pi default
```

Or create a `.env` file in `app-ui/`:
```
SSS2_SERIAL_PORT=/dev/tty.usbmodem40768801
```

### Default Serial Port

- **Mac**: `/dev/tty.usbmodem40768801`
- **Linux/Raspberry Pi**: `/dev/ttyACM0`

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/catalog` - Get peripheral catalog
- `GET /api/sss2/state` - Get device state
- `PUT /api/sss2/state` - Update device state
- `POST /api/sss2/ignition` - Toggle ignition (body: `{"on": true/false}`)
- `GET /api/snapshots` - List snapshots
- `POST /api/snapshots` - Create snapshot (body: `{"label": "optional"}`)
- `POST /api/snapshots/{id}/revert` - Revert to snapshot
- `DELETE /api/snapshots/{id}` - Delete snapshot

## Testing

```bash
cd app-ui
pytest tests/
```

## Deployment to Raspberry Pi

1. **On your development machine:**
   ```bash
   ./scripts/build-ui.sh
   ```

2. **Copy `app-ui/` to Raspberry Pi:**
   ```bash
   scp -r app-ui pi@raspberrypi.local:~/sss2-gui/
   ```

3. **On Raspberry Pi:**
   ```bash
   cd ~/sss2-gui/app-ui
   pip install -r requirements.txt
   python main.py
   ```

4. **Access from browser:**
   ```
   http://raspberrypi.local:8000
   ```

**Note:** Node.js is NOT required on the Raspberry Pi. Only Python is needed in production.

## Development

### Backend Structure

- `routers/` - API route handlers
- `services/` - Business logic layer
- `middleware/` - Orchestrator for service coordination
- `store/` - File-based JSON storage
- `tests/` - pytest tests

### Frontend Structure

- `src/lib/api/` - API client
- `src/lib/stores/` - Svelte stores
- `src/lib/components/` - Reusable components
- `src/lib/pages/` - Page components

## Features

- ✅ 16 Potentiometers configuration (J24:1-12, J18:11-12, J24:15-16)
- ✅ Wiper position control (0-255, 0.0V-5.0V)
- ✅ Terminal connection toggles (Term A, Term B, Wiper)
- ✅ Application and wire color configuration
- ✅ Snapshot management (create/list/revert/delete)
- ✅ Ignition toggle
- ✅ Touch-friendly UI (min 44px hit targets)
- ✅ Dark theme with Tailwind CSS

## Requirements

- Python 3.8+
- Node.js 16+ (only for development, not needed in production)
- npm or yarn
