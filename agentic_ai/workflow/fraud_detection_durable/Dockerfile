# Fraud Detection Durable Workflow
# Multi-stage build: React UI + Python Worker/Backend
# DTS runs as sidecar container in Container Apps
# Build context: agentic_ai/ (parent dir, for shared observability module)

# ============================================================================
# Stage 1: Build React Frontend
# ============================================================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy frontend package files
COPY workflow/fraud_detection_durable/ui/package*.json ./

# Install dependencies
RUN npm ci

# Copy frontend source
COPY workflow/fraud_detection_durable/ui/ ./

# Build React app (Vite outputs to 'dist/')
RUN npm run build

# ============================================================================
# Stage 2: Python Backend with Frontend Assets
# ============================================================================
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files first for caching
COPY workflow/fraud_detection_durable/pyproject.toml ./

# Install Python dependencies
RUN uv pip install --system -e .

# Copy application code
COPY workflow/fraud_detection_durable/*.py ./
COPY workflow/fraud_detection_durable/start.sh ./
RUN chmod +x /app/start.sh

# Copy shared observability module
COPY observability /app/observability

# Copy built frontend from previous stage (Vite outputs to 'dist')
COPY --from=frontend-builder /app/frontend/dist ./static

# Expose ports
# 8002 - FastAPI Backend (serves both API and UI)
EXPOSE 8002

# Environment variables (can be overridden)
# DTS_ENDPOINT should point to the sidecar container
ENV DTS_ENDPOINT="http://localhost:8080"
ENV DTS_TASKHUB="default"
ENV PYTHONUNBUFFERED=1
ENV BACKEND_PORT=8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

CMD ["/app/start.sh"]
