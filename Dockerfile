# ---- base: runtime dependencies only ----
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
RUN useradd --create-home --uid 10001 appuser
COPY requirements.txt .
RUN pip install -r requirements.txt

# ---- test: adds pytest/flake8 and the test suite ----
FROM base AS test
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt
COPY . .
USER appuser
CMD ["pytest", "-v", "-p", "no:cacheprovider"]

# ---- runtime: production image (default target) ----
FROM base AS runtime
COPY app.py ACEest_Fitness.py ./
COPY aceest ./aceest
RUN mkdir /app/data && chown appuser:appuser /app/data
# Version information, passed in by Jenkins. Declared late so that a new version
# does not invalidate the cached layers above.
ARG APP_VERSION=dev
ARG GIT_COMMIT=unknown
LABEL org.opencontainers.image.title="aceest-fitness" \
      org.opencontainers.image.description="ACEest Fitness & Gym Flask API" \
      org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.revision="${GIT_COMMIT}"
ENV ACEEST_DB=/app/data/aceest_fitness.db \
    APP_VERSION=${APP_VERSION} \
    GIT_COMMIT=${GIT_COMMIT} \
    GUNICORN_CMD_ARGS="--access-logfile=- --worker-tmp-dir=/dev/shm"
# numeric UID, so that Kubernetes can verify runAsNonRoot
USER 10001
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health')" || exit 1
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
