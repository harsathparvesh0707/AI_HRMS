FROM python:3.10.12-slim

# -------------------------------------------------------------------
# Python runtime settings
# -------------------------------------------------------------------
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

# -------------------------------------------------------------------
# System dependencies (needed for numpy, scipy, sklearn, torch)
# -------------------------------------------------------------------
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# -------------------------------------------------------------------
# Upgrade pip tooling FIRST
# -------------------------------------------------------------------
RUN pip install --upgrade pip setuptools wheel

# -------------------------------------------------------------------
# Install Python dependencies
# Torch CPU index must be available before pip resolves deps
# -------------------------------------------------------------------
COPY requirements.txt .

RUN pip install \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r requirements.txt

# -------------------------------------------------------------------
# Copy application code
# -------------------------------------------------------------------
COPY . .

ENV PYTHONPATH=/app
EXPOSE 8000
