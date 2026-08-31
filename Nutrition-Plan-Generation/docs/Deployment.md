# Deployment

> **Document Version:** 1.0.0
> **Status:** MVP Design

---

# 1. Overview

The Nutrition AI System is designed using a containerized architecture to simplify development, testing, and deployment.

For the MVP, the system can be deployed on a single server using Docker Compose.

Future versions can be migrated to cloud platforms such as AWS or Azure with minimal architectural changes.

---

# 2. Deployment Architecture

```
                    Internet
                         │
                         ▼
                  Nginx Reverse Proxy
                         │
                ┌────────┴────────┐
                ▼                 ▼
          Frontend (React)   FastAPI Backend
                                     │
                                     ▼
                           LangGraph Workflow
                                     │
                                     ▼
                          Local Food Repository
                                     │
                                     ▼
                           OpenAI / Gemini API
```

---

# 3. MVP Deployment

The MVP consists of four main services:

```
Docker Compose

│

├── Frontend

├── FastAPI Backend

├── Nginx

└── Redis (Optional)
```

At this stage, the food dataset is stored locally as a Parquet/CSV file and loaded into memory during application startup.

No external database is required.

---

# 4. Technology Stack

| Layer | Technology |
|---------|------------|
| Frontend | React |
| Backend | FastAPI |
| AI Workflow | LangGraph |
| LLM Framework | LangChain |
| Dataset | Pandas + Parquet |
| Reverse Proxy | Nginx |
| Containerization | Docker |
| Deployment | Docker Compose |

---

# 5. Deployment Workflow

```
Developer

↓

Git Repository

↓

Docker Build

↓

Docker Image

↓

Docker Compose

↓

Running Application
```

---

# 6. Docker Containers

The application is divided into separate containers.

```
Frontend Container

↓

Backend Container

↓

Nginx Container
```

Future versions may add:

- PostgreSQL
- Redis
- Monitoring Stack
- Vector Database

---

# 7. Configuration Management

All environment-specific values are stored in a `.env` file.

Examples include:

- API Keys
- LLM Model Name
- File Paths
- Allowed Origins (CORS)
- Logging Level

Sensitive information should never be committed to source control.

---

# 8. Startup Sequence

```
Start Containers

↓

Load Configuration

↓

Load Food Dataset

↓

Initialize LangGraph

↓

Register API Routes

↓

Start FastAPI

↓

Application Ready
```

The food dataset is loaded once during startup to avoid repeated disk access during requests.

---

# 9. Logging

The backend logs:

- Incoming requests
- Workflow execution
- Node execution time
- Errors
- Validation failures

Logs help monitor system behavior and simplify debugging.

---

# 10. Monitoring (Future)

Future deployments may integrate:

- Prometheus
- Grafana
- OpenTelemetry

Metrics may include:

- Request latency
- Workflow duration
- LLM response time
- Token usage
- Error rates

---

# 11. Security

Security considerations include:

- JWT authentication
- HTTPS
- Secure API key storage
- CORS configuration
- Rate limiting
- Input validation

Passwords must be hashed before storage.

---

# 12. Scalability

The architecture is designed to scale horizontally.

Future deployment may separate:

```
Frontend

↓

API Gateway

↓

FastAPI Instances

↓

LangGraph Workers

↓

Food Database

↓

LLM Provider
```

Additional workers can process multiple nutrition requests concurrently.

---

# 13. Future Cloud Deployment

The current architecture can be migrated to cloud infrastructure.

Possible deployment targets:

- AWS
- Microsoft Azure
- Google Cloud Platform

Potential cloud services:

| Component | Cloud Service |
|------------|---------------|
| Containers | Docker / Kubernetes |
| Compute | EC2 / Azure VM |
| Storage | S3 / Azure Blob Storage |
| Database | PostgreSQL |
| Cache | Redis |
| Monitoring | Cloud Monitoring |

---

# 14. Backup Strategy

Future versions should include:

- Scheduled dataset backups
- Configuration backups
- User data backups
- Generated meal plan backups

---

# 15. Deployment Checklist

Before deployment:

- Docker images built successfully.
- Environment variables configured.
- Food dataset available.
- API keys configured.
- CORS configured.
- HTTPS enabled (Production).
- Health endpoint verified.

---

# 16. Design Decisions

| Decision | Reason |
|----------|--------|
| Docker Compose | Simple local deployment |
| Local dataset | Fast MVP development |
| In-memory loading | Better runtime performance |
| Nginx reverse proxy | Secure request routing |
| Environment variables | Secure configuration |
| Containerized architecture | Easy migration to cloud |

---

# 17. Future Improvements

Future versions may introduce:

- Kubernetes deployment
- Auto Scaling
- Redis caching
- PostgreSQL database
- Distributed LangGraph workers
- CI/CD pipelines
- Blue-Green deployments
- GPU-enabled inference servers

These enhancements can be adopted without major changes to the application's architecture.

---

# 18. Summary

The Nutrition AI System uses a containerized deployment architecture centered around FastAPI, LangGraph, and Docker Compose.

For the MVP, the application relies on a locally stored food dataset loaded into memory, enabling rapid development and efficient inference without the complexity of managing a database.

The deployment strategy is intentionally modular, allowing future migration to cloud-native infrastructure while preserving the existing application architecture.

---

# Next Document

➡ **12_Future_Work.md**