FROM python:3.12-slim

WORKDIR /app

# Install dependencies first — layer is cached unless requirements change
COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

# Copy only what the API needs
COPY api/       ./api/
COPY player_scanner/ ./player_scanner/
COPY backend/   ./backend/
COPY db/        ./db/

EXPOSE 8080

# Cloud Run injects $PORT (default 8080)
CMD python -m uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8080}
