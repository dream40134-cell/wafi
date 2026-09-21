# --- builder stage -----------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build
COPY pyproject.toml ./
COPY src ./src

RUN pip install --no-cache-dir --prefix=/install .

# --- final stage ---------------------------------------------------------
FROM python:3.11-slim

RUN groupadd --gid 1000 wafi && \
    useradd --uid 1000 --gid wafi --shell /bin/false --create-home wafi

COPY --from=builder /install /usr/local
COPY --from=builder /build/src /app/src

WORKDIR /app
ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1

USER wafi

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request as u; u.urlopen('http://localhost:8000/ready', timeout=2)" || exit 1

EXPOSE 8000

# exec form -> uvicorn receives SIGTERM directly for a clean shutdown
CMD ["uvicorn", "wafi.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
