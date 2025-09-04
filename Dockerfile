FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

RUN useradd --create-home appuser

# data directory exists and is writable
RUN mkdir -p /app/data && chown -R appuser:appuser /app

# Copy application code **after creating user**
COPY --chown=appuser:appuser . .

EXPOSE 5001

USER appuser

ENTRYPOINT ["python", "app.py"]
