# Sentinel Drive AI

Sentinel Drive AI is a distributed AI-based safety platform designed to detect driver drowsiness in real time using computer vision and facial landmark analysis.

The system leverages a Python-based AI microservice to analyze live video input and detect fatigue indicators such as prolonged eye closure, abnormal blink rate, yawning, and head pose deviation. Detected risk events are sent to a Spring Boot backend service responsible for persistence, analytics, and system-level orchestration.

This project demonstrates the integration of applied artificial intelligence with enterprise-grade distributed system architecture.

**Full project description (math, parameters, architecture, LinkedIn-ready):** see **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)** — EAR/MAR/tilt formulas, configurable parameters, risk engine, and backend objectives.

---

## 📋 Project status and next steps

**Done so far**

- **Phase 1:** Monorepo, Docker (AI + Backend + PostgreSQL), `docker-compose`, env config.
- **Phase 2 (AI microservice):** OpenCV + MediaPipe Face Landmarker, EAR/MAR/head pose (6-point MAR for yawn), risk engine (levels, sustained-yawn logic, audio/visual alerts), pipeline (camera/stream), REST API with health, metrics, pipeline start/stop, event contract, retry when sending to backend. OpenAPI at `/docs`. **Live dashboard** at `/dashboard`: MJPEG stream, metrics sidebar, status bar over video, same green/red status on frame and in UI, audible repeating alert, Start/Stop without leaving the page.
- **Backend (partial Phase 3):** Spring Boot app, JPA + PostgreSQL, **Risk Event** entity and repository, **POST /api/v1/risk-events** (ingestion with validation, timestamp and `session_id` compatible with AI payload). Events are persisted to the `risk_events` table.

**End-to-end flow (working)**

1. Start stack: `docker-compose up` (or AI service locally with webcam; backend + Postgres in Docker).
2. Start pipeline: open `http://localhost:8000/api/v1/pipeline/start` or `curl -X POST http://localhost:8000/api/v1/pipeline/start`.
3. AI service reads video (e.g. webcam), detects face, computes EAR/MAR/head pose, emits risk events and POSTs them to `http://backend:8080/api/v1/risk-events` (or `http://localhost:8080` when AI runs locally).
4. Backend returns 201 and stores the event in PostgreSQL.

**Where to continue**

Use **CHECKLIST.md** for the full list. Suggested next steps:

- **Backend:** Session entity and APIs; list/filter risk events; analytics; Swagger; optional Flyway/Liquibase; Spring Security.
- **Integration:** Document the flow in README (e.g. diagram); add API examples (curl/Postman).
- **UX/Docs:** Local run instructions (already in README); **live dashboard** at `/dashboard` (done); state educational/portfolio use.
- **Polish:** Error handling, security review, tests, optional CI.

---

## 🏃 Quick Start (Docker)

From the project root:

```bash
docker-compose up --build
```

Or use the Makefile: `make up` to start, `make down` to stop, `make prune` or `make prune-all` to stop and remove volumes. For the backend: `make build`, `make test`, `make clean`.

This starts PostgreSQL, the Spring Boot backend, and the Python AI microservice. **For testing the full stack, always run inside Docker** (`docker-compose up`). Optional: copy `.env.example` to `.env` to override ports or credentials.

- **AI service:** http://localhost:8000 (e.g. `GET /health`, `GET /docs` for OpenAPI)
- **Live dashboard:** http://localhost:8000/dashboard (webcam + metrics and alerts; start the pipeline first)
- **Backend:** http://localhost:8080 (e.g. `GET /actuator/health`)
- **PostgreSQL:** `localhost:5432` (default user/db: `sentineldrive`)

---

## 🐍 Running the AI service locally (Python)

To run the AI microservice on your machine (e.g. with a local webcam):

1. **Create and activate a virtual environment** (recommended):

   ```bash
   cd ai-service
   python3 -m venv .venv
   source .venv/bin/activate   # Linux/macOS
   # or:  .venv\Scripts\activate   # Windows
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables** (optional): copy `.env.example` from the project root to `.env` and set `BACKEND_URL`, `VIDEO_SOURCE` (e.g. `0` for default camera), and thresholds.

4. **Run the service:**

   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Start the video pipeline** (when using a camera): open `http://localhost:8000/api/v1/pipeline/start` in the browser or `curl -X POST http://localhost:8000/api/v1/pipeline/start` (GET and POST are both accepted). Use `GET /api/v1/metrics` for live metrics and `GET` or `POST /api/v1/pipeline/stop` to stop.

API docs (OpenAPI/Swagger): http://localhost:8000/docs

**Troubleshooting — `No matching distribution found for mediapipe` on macOS**

MediaPipe does not provide wheels for every macOS + Python combination (e.g. Python 3.12 on macOS often has no wheel). Use **Python 3.10 or 3.11** when creating the venv (MediaPipe supports 3.8–3.11 on macOS).

1. **Install Python 3.11** (if not already installed). With [Homebrew](https://brew.sh):
   ```bash
   brew install python@3.11
   ```

2. **Create the venv** using the Homebrew Python (paths may vary: Intel Mac often `/usr/local`, Apple Silicon `/opt/homebrew`):
   ```bash
   cd ai-service
   # Apple Silicon (M1/M2/M3):
   /opt/homebrew/opt/python@3.11/bin/python3.11 -m venv .venv
   # Intel Mac (if different, run: brew --prefix python@3.11):
   # /usr/local/opt/python@3.11/bin/python3.11 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
   To see your Homebrew Python path: `brew --prefix python@3.11`.

- **Or run the AI service in Docker** (no local MediaPipe needed): use the full stack with `docker-compose up` and, for webcam on macOS, follow Option B below but run the AI service inside Docker without the pipeline, or use a pre-recorded video source via `VIDEO_SOURCE` (e.g. path to a file).

---

## 📷 Testing with your webcam

To see real-time detection using your computer's camera:

### Option A: Linux (Docker with camera access)

1. Create a `.env` file at the project root (if you don't have one) and set:
   ```bash
   VIDEO_SOURCE=0
   ```

2. In `docker-compose.yml`, under the `ai-service` service, add the video device passthrough (adjust `/dev/video0` if your camera uses a different device):
   ```yaml
   ai-service:
     ...
     devices:
       - "/dev/video0:/dev/video0"
   ```

3. Start the services and start the pipeline:
   ```bash
   docker-compose up -d
   curl -X POST http://localhost:8000/api/v1/pipeline/start
   ```

4. Watch metrics in real time:
   ```bash
   watch -n 0.5 'curl -s http://localhost:8000/api/v1/metrics'
   ```
   Or open http://localhost:8000/docs in your browser and use the endpoints there.

### Option B: macOS / Windows (AI service local, rest in Docker)

On macOS and Windows, Docker cannot access the host webcam. Run only the **AI service on your machine** and keep the rest (backend + Postgres) in Docker.

1. Start only the backend and Postgres:
   ```bash
   docker-compose up -d postgres backend
   ```

2. On your machine, set up the AI service Python environment and use the camera:
   ```bash
   cd ai-service
   python3 -m venv .venv
   source .venv/bin/activate    # macOS/Linux
   # .venv\Scripts\activate    # Windows
   pip install -r requirements.txt
   ```

3. Set the backend URL (reachable from the host) and start the AI service:
   ```bash
   export BACKEND_URL=http://localhost:8080
   export VIDEO_SOURCE=0
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. In another terminal, start the video pipeline (uses the default webcam):
   ```bash
   curl -X POST http://localhost:8000/api/v1/pipeline/start
   ```

5. View live metrics:
   ```bash
   curl -s http://localhost:8000/api/v1/metrics
   ```

---

## 🖥 Live dashboard (browser)

A **browser-based live view** is available at **http://localhost:8000/dashboard** (or http://localhost:8000/). It shows the webcam stream with metrics and status in three places: **on the image** (top-left, drawn by the AI service), a **bar over the video** (bottom), and the **sidebar** (EAR, MAR, head pose, frame count, status). All three show the same status: green **“It’s all good”** when there’s no recent alert, or the alert text in red when there is (with a 5-second cooldown after each alert). An **audible alert** (repeating beeps) plays while the status is red and stops when everything is OK again. **Start pipeline** and **Stop pipeline** run via the API without leaving the dashboard.

**How to use**

1. Start the AI service (Docker or locally with webcam).
2. Open **http://localhost:8000/dashboard** in your browser.
3. Click **Start pipeline** so the camera and detection start (you stay on the dashboard).
4. The video appears in the main area; EAR, MAR, head pose, frame count and status update in real time. Click **Stop pipeline** to stop without leaving the page.

The dashboard uses the **MJPEG** stream (`GET /api/v1/stream`) and polls `GET /api/v1/metrics` every 400 ms. The pipeline draws EAR, MAR, tilt and status (green/red) on each frame before streaming. For the alert sound to work, interact with the page first (e.g. click once).

**Note:** In local mode (Option B), the Face Landmarker model must be present at `ai-service/face_landmarker.task`. Download it once:
```bash
curl -fSL -o ai-service/face_landmarker.task \
  "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
```
Or set `FACE_LANDMARKER_MODEL_PATH` to the path of the `.task` file if you keep it elsewhere.

---

## 📄 Documentation

- **README.md** (this file) — quick start, run instructions, status.
- **PROJECT_OVERVIEW.md** — complete project description in English: EAR/MAR/tilt math, parameters, risk engine, backend goals; suitable as a base for articles or LinkedIn.
- **CHECKLIST.md** — implementation checklist and next steps.
- **scripts/md2pdf.py** — convert Markdown files to PDF (`pip install -r scripts/requirements-md2pdf.txt`, then `python scripts/md2pdf.py README.md -o README.pdf`).

---

## 🚀 Core Capabilities

- Real-time facial landmark detection (MediaPipe)
- Eye Aspect Ratio (EAR) computation for fatigue detection (see PROJECT_OVERVIEW.md for formulas)
- Yawn detection via Mouth Aspect Ratio (MAR), 6-point formula
- Head pose estimation (tilt/roll and yaw)
- Risk-level scoring engine
- Audio and visual alert system
- Event-driven communication between services
- Persistent risk history tracking
- Live dashboard in the browser: webcam feed with on-screen metrics, unified status (green “It’s all good” / red alert) on frame, overlay bar and sidebar, and repeating audible alert until OK
- Modular and scalable architecture

---

## 🏗 Distributed Architecture

The platform is composed of independent services:

### AI Microservice (Python)

- Computer vision processing
- Feature extraction
- Fatigue risk classification
- REST/gRPC event publishing

### Backend Service (Java - Spring Boot)

- Event ingestion
- Risk persistence (PostgreSQL)
- Session management
- REST API exposure
- Authentication & security layer
- System observability

The system is containerized using Docker and designed for scalability and production-oriented patterns.

---

## 🧠 Technologies

**AI Layer**

- Python
- OpenCV
- MediaPipe
- NumPy
- FastAPI

**Backend Layer**

- Java 21
- Spring Boot
- Spring Data JPA
- Spring Security
- PostgreSQL

**Infrastructure**

- Docker
- Docker Compose
- Swagger / OpenAPI
- Structured logging

---

## 🎯 Objective

The goal of this project is to demonstrate how real-time AI processing can be integrated into a distributed architecture suitable for safety-critical applications.

Sentinel Drive AI is intended for educational, research, and portfolio purposes and simulates automated safety responses in controlled environments.

---

_Sentinel Drive AI_ — distributed driver drowsiness detection platform.  
**Author:** Valter Sales · **Date:** 2025-02-18 · **Last Update:** 2025-02-18  

To pick up the project later, see **CHECKLIST.md** and the “Project status and next steps” section above. For a full technical and narrative description (including math and parameters), see **PROJECT_OVERVIEW.md**.
