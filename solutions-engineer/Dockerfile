FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Railway injects the PORT env var dynamically. Local default is 8000.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}