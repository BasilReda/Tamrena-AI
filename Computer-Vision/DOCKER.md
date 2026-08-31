# AI-GYM Docker Setup Guide

This guide explains how to run the entire **AI-GYM** application (FastAPI Backend + React Frontend) using Docker and Docker Compose.

---

## 🚀 Quick Start with Docker Compose

### 1. Build and Start Container Services
Run the following command in the project root directory:

```bash
docker-compose up --build -d
```

- **Backend API**: `http://localhost:8000`
- **Frontend App**: `http://localhost:5173`
- **API Health Check**: `http://localhost:8000/api/health`

---

## 🛠 Useful Docker Commands

### Stop Container Services
```bash
docker-compose down
```

### View Live Logs
```bash
# All services
docker-compose logs -f

# Backend service logs
docker-compose logs -f backend

# Frontend service logs
docker-compose logs -f frontend
```

### Rebuild Containers After Code Updates
```bash
docker-compose up --build -d
```

---

## 📦 Pushing to GitHub & Repository Check-in

The following files are now configured for Docker deployment:

- `Dockerfile` (Backend API container configuration)
- `frontend/Dockerfile` (React + Vite container configuration)
- `docker-compose.yml` (Service orchestrator)
- `.dockerignore` & `frontend/.dockerignore` (Build context optimization)

When pushing your code to GitHub, ensure these files are committed:

```bash
git add Dockerfile frontend/Dockerfile docker-compose.yml .dockerignore frontend/.dockerignore DOCKER.md
git commit -m "feat: Add Docker and Docker Compose configuration"
git push origin main
```
