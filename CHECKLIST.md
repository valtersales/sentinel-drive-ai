# Sentinel Drive AI — Implementation Checklist

Checklist to guide project implementation, in the suggested order of execution.

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

- [ ] Create `requirements.txt` (OpenCV, MediaPipe, NumPy, FastAPI, uvicorn)
- [ ] Set up virtual environment and add instructions to README
- [ ] Expose health check endpoint (e.g. `GET /health`)

### 2.2 Computer Vision

- [ ] Integrate video capture (live camera or stream)
- [ ] Integrate MediaPipe Face Mesh for facial landmarks
- [ ] Implement **EAR (Eye Aspect Ratio)** calculation for eye-closure detection
- [ ] Define threshold and time window for “prolonged blink”
- [ ] Implement **MAR (Mouth Aspect Ratio)** calculation for yawn detection
- [ ] Implement **head pose** estimation (tilt/rotation)
- [ ] Handle frames with no face detected (fallback/timeout)

### 2.3 Risk Engine

- [ ] Define “risk event” data model (level, type, timestamp, metrics)
- [ ] Implement **risk-level scoring** based on EAR, MAR, and head pose
- [ ] Define risk levels (e.g. low, medium, high, critical)
- [ ] Implement **audio alerts** (e.g. beep when threshold is exceeded)
- [ ] Implement **visual alerts** (e.g. overlay on frame or UI notification)

### 2.4 API and Communication

- [ ] Expose REST endpoint to send risk events to the backend (or gRPC)
- [ ] Document event contract (payload, required fields)
- [ ] Configure backend URL via environment variable
- [ ] Handle retry/backoff when communication with backend fails
- [ ] (Optional) Document AI service API with OpenAPI/Swagger

---

## 3. Backend Service (Java — Spring Boot)

### 3.1 Base Project

- [ ] Create Spring Boot project (Java 21)
- [ ] Configure dependencies: Spring Data JPA, Spring Security, Spring Web, PostgreSQL driver
- [ ] Configure `application.yml`/`.properties` (profiles: dev, prod)
- [ ] Connect to PostgreSQL (local and via Docker)
- [ ] Expose health check (e.g. Actuator `/actuator/health`)

### 3.2 Data Model and Persistence

- [ ] Define **Risk Event** entity (level, type, timestamp, session_id, metrics, etc.)
- [ ] Define **Session** entity (driver/usage session)
- [ ] Create JPA repositories for Risk Event and Session
- [ ] Create migrations (Flyway/Liquibase) for initial schema
- [ ] Implement **event ingestion** (endpoint or consumer that receives events from AI service)
- [ ] Validate payload and persist events to PostgreSQL

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

- [ ] AI service sends risk events to the backend in real time
- [ ] Backend validates and persists events; returns appropriate status
- [ ] Handle scenario when backend is unavailable (retry, queue, or local log)
- [ ] Document end-to-end flow (diagram or description in README)
- [ ] Test full flow: video → detection → event → persistence → query via API

---

## 5. User Experience and Documentation

- [ ] Local run instructions (prerequisites, env vars, commands) in README
- [ ] API call examples (curl or Postman)
- [ ] (Optional) Minimal UI to view alerts or history (e.g. static page or SPA)
- [ ] State clearly in README that the project is educational/portfolio and for controlled environments

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
