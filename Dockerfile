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
COPY app.py .
COPY aceest ./aceest
RUN mkdir /app/data && chown appuser:appuser /app/data
ENV ACEEST_DB=/app/data/aceest_fitness.db
USER appuser
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health')" || exit 1
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
