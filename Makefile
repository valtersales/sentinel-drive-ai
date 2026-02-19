# Sentinel Drive AI - simplified Makefile
# Maven (backend) and Docker Compose targets

.PHONY: help build test clean docker-up docker-down docker-prune

help:
	@echo "Sentinel Drive AI - targets:"
	@echo "  make build        - build backend with Maven"
	@echo "  make test         - run backend tests"
	@echo "  make clean        - Maven clean + remove backend target"
	@echo "  make up 		   - start stack (docker-compose up -d)"
	@echo "  make down  	   - stop and remove containers"
	@echo "  make prune 	   - down + prune volumes/networks"
	@echo "  make prune-all    - down + prune all resources"

# --- Maven (backend) ---
build:
	mvn -f backend/pom.xml package -DskipTests

test:
	mvn -f backend/pom.xml test

clean:
	mvn -f backend/pom.xml clean

# --- Docker Compose ---
up:
	docker-compose up -d --build

down:
	docker-compose down

backend-up:
	docker-compose build backend && docker-compose up -d backend postgres

prune: down
	docker-compose down -v
	docker image prune -f

prune-all: down
	docker-compose down -v
	docker image prune -f
	docker container prune -f
	docker volume prune -f
	docker network prune -f
	docker system prune -f

ai-service-local-up:
	cd ai-service && source .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000