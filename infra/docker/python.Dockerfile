#
# Python image of Agilina. One file, several targets:
#
#   dev   everything needed to work: all workspace dependencies and the dev tools
#         (pytest, ruff, mypy, import-linter). The source is bind-mounted at /app,
#         so code changes need no rebuild. Used by the API, the transcription
#         service, the agent worker and the `tools` service of the compose file.
#   api   production image of the API: only its own dependencies, the code
#         installed (not mounted), no uv, and a non-root user.
#
# Build context: the repository root (the workspace needs shared/ and the
# pyproject.toml files of every member).
ARG PYTHON_VERSION=3.12

# --------------------------------------------------------------------- base --
# Time zones: the API validates and converts IANA zones (the daily's capture time zone,
# AD-31) with the system tzdata (/usr/share/zoneinfo), which bookworm-slim ships; the PyPI
# tzdata package is only locked for Windows. Changing the base image (here or in the `api`
# target) must keep it, or every zone fails with ZoneInfoNotFoundError in production. CI
# runs on Ubuntu, which has it too, so it would not notice.
FROM python:${PYTHON_VERSION}-slim-bookworm AS base
COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /uvx /bin/

# The virtualenv lives outside /app so that bind-mounting the repository over
# /app in development does not hide it.
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1
WORKDIR /app

# Only the manifests and the lock file: this layer is rebuilt when dependencies change,
# not on every edit. `--locked` below fails if uv.lock does not match pyproject.toml
# (run `make lock`), so an image never silently resolves different versions.
COPY pyproject.toml uv.lock ./
COPY shared/pyproject.toml shared/pyproject.toml
COPY api/pyproject.toml api/pyproject.toml
COPY agent/pyproject.toml agent/pyproject.toml
COPY stt/pyproject.toml stt/pyproject.toml

# ---------------------------------------------------------------------- dev --
FROM base AS dev
RUN uv sync --locked --all-packages --all-groups --no-install-workspace
# The workspace members are imported from the bind-mounted source, not installed.
ENV PYTHONPATH=/app/shared/src:/app/api/src:/app/agent/src:/app/stt/src \
    HOME=/tmp
CMD ["bash"]

# ---------------------------------------------------------------- api-build --
FROM base AS api-build
RUN uv sync --locked --package agilina-api --no-dev --no-install-workspace
COPY shared/ shared/
COPY api/ api/
RUN uv sync --locked --package agilina-api --no-dev --no-editable

# ---------------------------------------------------------------------- api --
# Same base as `base`, for its system tzdata (see the note there and AD-31).
FROM python:${PYTHON_VERSION}-slim-bookworm AS api
RUN useradd --system --create-home --uid 10001 agilina
COPY --from=api-build /opt/venv /opt/venv
# Alembic reads these from the working directory; the code itself is in the venv.
COPY api/alembic.ini /app/api/alembic.ini
COPY api/migrations /app/api/migrations
ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1
WORKDIR /app/api
USER agilina
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
CMD ["uvicorn", "agilina_api.bootstrap.app:app", "--host", "0.0.0.0", "--port", "8000"]
