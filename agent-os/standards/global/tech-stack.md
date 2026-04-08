## Tech Stack

Defines the technical stack for the project. Serves as a reference for all team members and ensures consistency.

### Framework & Runtime
- **Application Framework:** FastAPI (async, modern, OpenAPI-native)
- **MCP Server:** FastMCP
- **Language/Runtime:** Python 3.12+ (preference 3.13+)
- **Package Manager:** UV (fast Rust-based package manager)
- **Project Management:** `pyproject.toml` (single repo per project)

### Frontend
- **UI Framework:** Streamlit (minimalist, for test/admin UIs)
- **CustomTkinter:** For Desktop Applications

### Database & Storage
- **Database:** SQL Server 2019 Standard Edition (LocalDB for development)
- **ORM/Query Builder:** SQLAlchemy 2.0 (async) + Alembic (migrations)

### Testing & Quality
- **Test Framework:** pytest + pytest-asyncio
- **Coverage:** pytest-cov
- **Linting:** Ruff (replaces flake8, isort, pyupgrade in one tool)
- **Formatting:** Ruff format
- **Type Checking:** mypy or Pyright

### Deployment & Infrastructure
- **Containerization:** Podman (rootless, Docker-compatible)
- **Hosting:** Self-hosted
- **Repository:** Azure DevOps Repos
- **CI/CD:** Azure Pipelines
- **Reverse Proxy:** NGINX

### Third-Party Services
- **Error Tracking:** Sentry
- **Logging:** Structlog (structured logging)

### Development Tools
- **Task Runner:** UV scripts in `pyproject.toml`
- **API Documentation:** Auto-generated via FastAPI (Swagger)
- **Environment Management:** UV (automatic virtual envs)
- **Secret Management:** python-dotenv
- **Changelog:** Keep a Changelog format (keepachangelog.com), entry per commit