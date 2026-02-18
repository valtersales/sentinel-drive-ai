# Sentinel Drive AI

Sentinel Drive AI is a distributed AI-based safety platform designed to detect driver drowsiness in real time using computer vision and facial landmark analysis.

The system leverages a Python-based AI microservice to analyze live video input and detect fatigue indicators such as prolonged eye closure, abnormal blink rate, yawning, and head pose deviation. Detected risk events are sent to a Spring Boot backend service responsible for persistence, analytics, and system-level orchestration.

This project demonstrates the integration of applied artificial intelligence with enterprise-grade distributed system architecture.

---

## 🏃 Quick Start (Docker)

From the project root:

```bash
docker-compose up --build
```

Or use the Makefile: `make up` to start, `make down` to stop, `make prune` or `make prune-all` to stop and remove volumes. For the backend: `make build`, `make test`, `make clean`.

This starts PostgreSQL, the Spring Boot backend, and the Python AI microservice. Optional: copy `.env.example` to `.env` to override ports or credentials.

- **AI service:** http://localhost:8000 (e.g. `GET /health`)
- **Backend:** http://localhost:8080 (e.g. `GET /actuator/health`)
- **PostgreSQL:** `localhost:5432` (default user/db: `sentineldrive`)

---

## 🚀 Core Capabilities

- Real-time facial landmark detection (MediaPipe)
- Eye Aspect Ratio (EAR) computation for fatigue detection
- Yawn detection via Mouth Aspect Ratio (MAR)
- Head pose estimation
- Risk-level scoring engine
- Audio and visual alert system
- Event-driven communication between services
- Persistent risk history tracking
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
