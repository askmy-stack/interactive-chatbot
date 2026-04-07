# ── Build stage ────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS base

WORKDIR /app

# System deps (for psutil wheel build)
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Install dependencies from pyproject.toml
COPY pyproject.toml .
RUN pip install --no-cache-dir uv && uv pip install --system .

# Copy source
COPY . .

# ── Runtime ────────────────────────────────────────────────────────────────────
EXPOSE 8000 8501

# Start FastAPI backend and Streamlit UI in the same container.
# For production split these into separate services in docker-compose.
CMD ["sh", "-c", \
  "uvicorn backend.main:app --host 0.0.0.0 --port 8000 & \
   streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true"]
