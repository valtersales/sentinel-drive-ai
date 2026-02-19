# Sentinel Drive AI — Implementation Checklist

Checklist to guide project implementation, in the suggested order of execution.

**Resuming the project:** See **README.md** → “Project status and next steps” for a short summary of what is done and the end-to-end flow. For a full project description (EAR/MAR/tilt math, parameters, backend objectives), see **PROJECT_OVERVIEW.md**. Then use the unchecked items below; suggested focus: backend Section 3.3 (list risk events, sessions, analytics), then 3.4 (Security), then 5–6.

---

## 1. Base Structure and Infrastructure

- [x] Define monorepo folder structure (e.g. `ai-service/`, `backend/`, `docker/`)
- [x] Configure Docker for the AI Microservice (Python)
- [x] Configure Docker for the Backend (Spring Boot)
- [x] Create `docker-compose.yml` orchestrating both services + PostgreSQL
- [x] Configure network and environment variables between containers
- [x] Ensure services start with `docker-compose up`

---

## 2. AI Microservice (Python)

### 2.1 Environment and Dependencies

- [x] Create `requirements.txt` (OpenCV, MediaPipe, NumPy, FastAPI, uvicorn)
- [x] Set up virtual environment and add instructions to README
- [x] Expose health check endpoint (e.g. `GET /health`)

### 2.2 Computer Vision

- [x] Integrate video capture (live camera or stream)
- [x] Integrate MediaPipe Face Mesh for facial landmarks
- [x] Implement **EAR (Eye Aspect Ratio)** calculation for eye-closure detection
- [x] Define threshold and time window for “prolonged blink”
- [x] Implement **MAR (Mouth Aspect Ratio)** calculation for yawn detection
- [x] Implement **head pose** estimation (tilt/rotation)
- [x] Handle frames with no face detected (fallback/timeout)

### 2.3 Risk Engine

- [x] Define “risk event” data model (level, type, timestamp, metrics)
- [x] Implement **risk-level scoring** based on EAR, MAR, and head pose
- [x] Define risk levels (e.g. low, medium, high, critical)
- [x] Implement **audio alerts** (e.g. beep when threshold is exceeded)
- [x] Implement **visual alerts** (e.g. overlay on frame or UI notification)

### 2.4 API and Communication

- [x] Expose REST endpoint to send risk events to the backend (or gRPC)
- [x] Document event contract (payload, required fields)
- [x] Configure backend URL via environment variable
- [x] Handle retry/backoff when communication with backend fails
- [x] (Optional) Document AI service API with OpenAPI/Swagger

---

## 3. Backend Service (Java — Spring Boot)

### 3.1 Base Project

- [x] Create Spring Boot project (Java 21)
- [x] Configure dependencies: Spring Data JPA, Spring Web, PostgreSQL driver, validation
- [ ] Configure **Spring Security** (see 3.4)
- [x] Configure `application.yml`/`.properties` (profiles: dev, prod)
- [x] Connect to PostgreSQL (local and via Docker)
- [x] Expose health check (e.g. Actuator `/actuator/health`)

### 3.2 Data Model and Persistence

- [x] Define **Risk Event** entity (level, type, timestamp, session_id, metrics, etc.)
- [ ] Define **Session** entity (driver/usage session)
- [x] Create JPA repository for Risk Event
- [ ] Create JPA repository for Session
- [ ] Create migrations (Flyway/Liquibase) for initial schema (currently using JPA `ddl-auto`)
- [x] Implement **event ingestion** (`POST /api/v1/risk-events` receives events from AI service)
- [x] Validate payload and persist events to PostgreSQL

### 3.3 REST API

- [ ] Expose API to list risk events (filters: session, period, level)
- [ ] Expose API to list/create sessions
- [ ] Expose API for analytics (e.g. summary per session, count by level)
- [ ] Document API with **Swagger/OpenAPI**
- [ ] Version API (e.g. `/api/v1/...`)

### 3.4 Security and Observability

- [ ] Configure **Spring Security** (authentication: JWT or Basic, as per scope)
- [ ] Protect ingestion and query endpoints
- [ ] Configure **structured logging** (JSON or standardized format)
- [ ] (Optional) Integrate metrics (Micrometer/Prometheus) and traces

---

## 4. Service Integration

- [x] AI service sends risk events to the backend in real time
- [x] Backend validates and persists events; returns appropriate status (201 Created)
- [x] Handle scenario when backend is unavailable (retry/backoff in AI service)
- [ ] Document end-to-end flow (diagram or description in README)
- [x] Test full flow: video → detection → event → persistence (query API not yet implemented)

---

## 5. User Experience and Documentation

- [x] Local run instructions (prerequisites, env vars, commands) in README
- [ ] API call examples (curl or Postman) for risk-events and future list/analytics endpoints
- [x] State clearly in README that the project is educational/portfolio and for controlled environments

- [x] **PROJECT_OVERVIEW.md** — full project description in English (EAR/MAR/tilt formulas, parameters, risk engine, backend objectives; base for articles/LinkedIn).

### 5.1 Live dashboard (browser) — webcam + metrics and alerts on screen

- [x] **Stream from AI service:** Expose a live video stream from the pipeline (e.g. **MJPEG** at `GET /api/v1/stream`, or **WebSocket** pushing frame + metadata). Reuse existing frame buffer or pipeline loop; optionally draw overlay (EAR/MAR/alert) on each frame before streaming.
- [x] **Dashboard page:** Provide a static page (e.g. `/dashboard` or `/` from the AI service) that embeds the stream (`<img src="...">` for MJPEG, or WebSocket + canvas/img for WebSocket) and shows metrics and alerts in dedicated areas (sidebar, cards, or overlay).
- [x] **Layout:** Organize on-screen elements: video feed prominent; EAR, MAR, head pose, risk level and last alert text clearly visible and updated in real time.
- [x] Document in README how to open the dashboard (URL and prerequisites: pipeline must be started).
- [x] **Status consistency and UX:** Same status text and colors (green “It’s all good” / red alert with 5s cooldown) on the frame overlay (OpenCV), HTML bar over video, and sidebar; repeating audible alert until OK; Start/Stop pipeline via JS without navigating away.

---

## 6. Refinements and Production

- [ ] Review error handling and log messages
- [ ] Review security settings (secrets, CORS, rate limiting if applicable)
- [ ] Ensure images/video are not persisted unnecessarily (privacy/GDPR)
- [ ] Automated tests: unit tests in backend and AI service (where it makes sense)
- [ ] (Optional) CI pipeline (build, tests, Docker image build)

---

## Legend

- **EAR:** Eye Aspect Ratio  
- **MAR:** Mouth Aspect Ratio  
- Items marked “(Optional)” can be done in a second phase.

Use this checklist as a guide; adjust order and scope according to project priorities.
