# Sentinel Drive AI — Project Overview

**A distributed, AI-based driver drowsiness detection platform using computer vision and facial landmark analysis.**

This document describes the project in full: architecture, mathematical foundations (EAR, MAR, head pose/tilt), configurable parameters, risk engine logic, and the role of each component. It also serves as a base for project presentations and articles (e.g. LinkedIn).

---

## 1. Introduction and Purpose

Sentinel Drive AI is a **distributed safety platform** that detects driver drowsiness and fatigue in real time. A Python AI microservice analyzes live video (webcam or stream), extracts facial metrics, and classifies risk. Detected events are sent to a Java/Spring Boot backend for persistence, analytics, and future system-level orchestration.

The project demonstrates **applied AI** (computer vision, geometric metrics) in an **enterprise-style** setup: microservices, REST APIs, event-driven communication, and containerized deployment. It is intended for **educational, research, and portfolio** use and simulates automated safety responses in controlled environments.

---

## 2. High-Level Architecture

The system has three main parts:

| Component | Technology | Role |
|-----------|------------|------|
| **AI Microservice** | Python, FastAPI, OpenCV, MediaPipe | Captures video, detects face, computes EAR/MAR/head pose, runs risk engine, sends events to backend, exposes live stream and dashboard |
| **Backend Service** | Java 21, Spring Boot, JPA, PostgreSQL | Receives risk events, validates and persists them; (future) sessions, analytics, authentication |
| **PostgreSQL** | Database | Stores risk events (and later sessions, users) |

Flow in short: **Video → AI (face + metrics + risk) → REST event → Backend → Database.** The AI service also exposes a **live dashboard** (MJPEG stream + metrics + alerts) and API for pipeline start/stop and metrics.

---

## 3. Mathematical Foundations: EAR, MAR, and Head Pose (Tilt)

The AI service uses **MediaPipe Face Mesh**, which provides 468 3D facial landmarks per frame. From these we compute three kinds of metrics.

### 3.1 Eye Aspect Ratio (EAR)

**EAR** is a scalar that drops when the eye closes and rises when it opens. It is robust to head distance because it uses ratios of distances.

**Formula (per eye):**

\[
\text{EAR} = \frac{\|p_2 - p_6\| + \|p_3 - p_5\|}{2 \cdot \|p_1 - p_4\|}
\]

- **Vertical segments:** \(\|p_2 - p_6\|\) and \(\|p_3 - p_5\|\) (upper-to-lower eyelid distances).
- **Horizontal segment:** \(\|p_1 - p_4\|\) (eye width between inner and outer corners).

**MediaPipe Face Mesh indices (0-based):**

- **Left eye:** \(p_1=33,\, p_2=160,\, p_3=158,\, p_4=133,\, p_5=153,\, p_6=144\)
- **Right eye:** \(p_1=362,\, p_2=385,\, p_3=387,\, p_4=263,\, p_5=373,\, p_6=380\)

**Implementation:** We compute EAR for left and right eyes in pixel coordinates, then take the **average** of both. If either denominator is too small, EAR is not computed for that frame.

**Typical values:** Open eye ≈ 0.25–0.35; closed eye &lt; 0.2. A threshold (e.g. **0.2**) is used to decide “eye closed”; prolonged closure (e.g. &gt; 0.5 s) is treated as drowsiness.

*Reference: Soukupová & Čech, “Real-Time Eye Blink Detection using Facial Landmarks” (2016).*

---

### 3.2 Mouth Aspect Ratio (MAR)

**MAR** measures mouth openness: it increases when the mouth opens (e.g. yawning) and is lower when the mouth is closed.

**6-point formula (used in this project):**

\[
\text{MAR} = \frac{\text{vertical\_left} + \text{vertical\_right}}{2 \cdot \text{horizontal}}
\]

- **Vertical:** distances from upper lip to lower lip on left and right (landmarks 13→312 and 14→317).
- **Horizontal:** distance between mouth corners (landmarks 78 and 308).

**MediaPipe indices:** Upper lip: 13, 14; lower lip: 312, 317; corners: 78, 308.

**Typical values:** Closed mouth ~0.14–0.16; open/yawn ~0.18 and above (often 0.2–0.5+). A **MAR threshold** (e.g. **0.16**) plus a **sustained duration** (e.g. 0.3 s) are used to reduce false positives from talking or smiling.

---

### 3.3 Head Pose: Tilt (Roll) and Yaw

Head pose is estimated from landmarks (no full 3D camera calibration). Two angles are derived:

**Tilt (roll)** — head leaning to the side:

- Left and right **eye centers** are computed as the mean of the left and right eye landmark indices.
- Vector **eye_vec = right_eye − left_eye** in normalized coordinates.
- **Tilt (radians)** = \(\arctan2(\text{eye\_vec}_y,\, \text{eye\_vec}_x)\); converted to degrees.
- Tilt &gt; **threshold** (e.g. 25°) is used as a risk indicator (e.g. head nodding or leaning).

**Yaw** — rough left/right rotation:

- **Eye center** = midpoint of left and right eye centers.
- **Nose tip** (index 4) offset from eye center in \(x\) is scaled (e.g. ×60) and clipped to about ±45°.
- Used for context; risk engine primarily uses **tilt** for alerts.

All coordinates use MediaPipe’s normalized \([0,1]\) space; pixel coordinates are used only where needed (e.g. EAR/MAR in pixels for consistency with the literature).

---

## 4. Configurable Parameters

These parameters control detection sensitivity and can be set via environment variables (and partly via the risk engine config).

| Parameter | Env var | Default | Description |
|-----------|---------|---------|-------------|
| **EAR threshold** | `EAR_THRESHOLD` | 0.2 | Eye is considered closed when EAR &lt; this value. |
| **EAR closure duration** | `EAR_CLOSURE_SECONDS` | 0.5 | Seconds the eye must stay closed to trigger a prolonged-blink (drowsiness) event. |
| **MAR threshold** | `MAR_THRESHOLD` | 0.16 | Mouth is considered “open” when MAR ≥ this (e.g. yawn). Tune between closed (~0.14) and open (~0.18) for your setup. |
| **MAR sustained duration** | `MAR_SUSTAINED_SECONDS` | 0.3–0.4 | MAR must stay above threshold for this long to count as yawn (reduces false positives). |
| **Head pose tilt threshold** | `HEAD_POSE_TILT_THRESHOLD_DEG` | 25.0 | Tilt (degrees) above which head pose is considered a risk. |
| **Event cooldown** | (risk engine) | 2.0 s | Minimum time between two alerts of the same type (eye closure, yawn, head pose). |
| **Backend retry** | `BACKEND_RETRY_MAX`, `BACKEND_RETRY_BACKOFF_SEC` | 5, 1.0 | Retries and backoff when sending events to the backend. |
| **Video source** | `VIDEO_SOURCE` | 0 | Default camera index; or URL (RTSP/HTTP) or file path. |
| **Backend URL** | `BACKEND_URL` | — | Backend base URL for `POST /api/v1/risk-events`. |

---

## 5. Risk Engine and Event Types

The **risk engine** consumes per-frame metrics (EAR, MAR, head pose) and produces **risk events** when conditions are met.

**Risk levels:** LOW, MEDIUM, HIGH, CRITICAL.

**Event types:**

- **EYE_CLOSURE** — prolonged eye closure (EAR &lt; threshold for ≥ `EAR_CLOSURE_SECONDS`). Severity: MEDIUM (&lt;1 s), HIGH (1–2 s), CRITICAL (≥2 s).
- **YAWN** — MAR ≥ threshold for ≥ `MAR_SUSTAINED_SECONDS`. Severity: MEDIUM or HIGH (e.g. MAR ≥ 0.20 → HIGH).
- **HEAD_POSE** — absolute tilt ≥ `HEAD_POSE_TILT_THRESHOLD_DEG`. Severity: MEDIUM (&lt;40°) or HIGH (≥40°).

Each event includes: level, type, timestamp (UTC), optional session_id, and a metrics dictionary (EAR, MAR, head pose, and any extra fields such as closure/sustained duration). Events are sent to the backend via **POST /api/v1/risk-events** and are subject to cooldown per type to avoid flooding.

**Alerts:** When a risk event is emitted, the system triggers an **audio alert** (e.g. beep) and **visual feedback** (overlay on the video and on the dashboard). The dashboard shows a unified status (e.g. green “It’s all good” or red alert text) and an optional repeating audible alert until the state is OK again.

---

## 6. AI Microservice in Detail

- **Video capture:** OpenCV; source from `VIDEO_SOURCE` (camera index, URL, or file).
- **Face detection and landmarks:** MediaPipe Face Landmarker (`.task` model); 468 landmarks per frame.
- **Feature extraction:** EAR (both eyes, averaged), MAR (6-point), head pose (tilt and yaw) from landmarks.
- **Risk engine:** Applies thresholds and time windows; emits risk events and triggers alerts.
- **Backend client:** HTTP client with retry/backoff; POSTs risk events to the backend.
- **REST API:** Health, metrics, pipeline start/stop, MJPEG stream; OpenAPI at `/docs`.
- **Dashboard:** Static page at `/dashboard`: embeds MJPEG stream, shows EAR/MAR/head pose/frame count and status, Start/Stop pipeline, optional audible alert.

---

## 7. Backend Service (Current and Planned)

**Currently implemented:**

- Spring Boot (Java 21), JPA, PostgreSQL.
- **Risk Event** entity and repository; table `risk_events`.
- **POST /api/v1/risk-events** — ingestion with validation; stores level, type, timestamp, session_id, metrics.
- Health check (e.g. Actuator).

**Planned objectives:**

- **Session entity and APIs** — represent a driver/usage session; link risk events to sessions; list/create sessions.
- **List and filter risk events** — by session, time range, level, type.
- **Analytics** — summaries per session, counts by level/type, trends.
- **API documentation** — Swagger/OpenAPI; versioned API (/api/v1/...).
- **Security** — Spring Security; authentication (e.g. JWT or Basic); protection of ingestion and query endpoints.
- **Schema migrations** — Flyway or Liquibase instead of (or in addition to) JPA ddl-auto.
- **Observability** — Structured logging; optional metrics (Micrometer/Prometheus) and tracing.

The backend is intended to be the **persistence and orchestration layer**: store all risk events, support sessions and analytics, and eventually authentication and system-level policies.

---

## 8. Live Dashboard and User Flow

1. Start the stack (e.g. `docker-compose up` or AI service locally with webcam).
2. Open **http://localhost:8000/dashboard**.
3. Click **Start pipeline** (or call `POST /api/v1/pipeline/start`). Camera and detection start; video appears with overlay (EAR, MAR, tilt, status).
4. Metrics and status update in real time (sidebar, bar over video, and on-frame overlay). If a risk is detected, status turns red and optional audible alert plays; after a short cooldown, status returns to green when OK.
5. Click **Stop pipeline** (or `POST /api/v1/pipeline/stop`) to stop without leaving the page.

The dashboard uses the **MJPEG** stream (`GET /api/v1/stream`) and polls `GET /api/v1/metrics` periodically.

---

## 9. Technologies Summary

**AI layer:** Python, OpenCV, MediaPipe, NumPy, FastAPI, uvicorn.  
**Backend layer:** Java 21, Spring Boot, Spring Data JPA, PostgreSQL (Spring Security and migrations planned).  
**Infrastructure:** Docker, Docker Compose, OpenAPI/Swagger, structured logging.

---

## 10. How to Run

- **Full stack:** `docker-compose up` (or `make up`). AI: http://localhost:8000, dashboard: http://localhost:8000/dashboard, backend: http://localhost:8080.
- **AI locally (e.g. with webcam):** Create venv in `ai-service`, `pip install -r requirements.txt`, set `BACKEND_URL` and `VIDEO_SOURCE`, run `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`. Start pipeline via dashboard or `POST /api/v1/pipeline/start`.
- **Face Landmarker model:** Download `face_landmarker.task` into `ai-service/` (see README) or set `FACE_LANDMARKER_MODEL_PATH`.

For detailed steps, troubleshooting (e.g. MediaPipe on macOS), and webcam options (Linux Docker vs macOS/Windows local AI), see **README.md** and **CHECKLIST.md**.

---

## 11. Summary

Sentinel Drive AI combines **real-time computer vision** (EAR, MAR, head pose from facial landmarks) with a **configurable risk engine** and **distributed architecture** (AI microservice + Java backend + PostgreSQL). The mathematical metrics are well-established in the literature; the implementation uses MediaPipe Face Mesh and configurable thresholds and time windows. The backend will expand into sessions, analytics, security, and observability. The project is suitable for education, portfolios, and controlled-environment demonstrations of AI-driven safety systems.

---

*Sentinel Drive AI — Project Overview. Author: Valter Sales. Last update: 2025-02-18.*
