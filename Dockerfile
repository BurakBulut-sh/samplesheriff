# SampleSheriff Docker Image
# Multi-stage build for a minimal production image

# Build stage
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir build && \
    mkdir -p src/samplesheriff && \
    touch src/samplesheriff/__init__.py && \
    python -m build --wheel

# Runtime stage
FROM python:3.11-slim

LABEL maintainer="SampleSheriff Contributors"
LABEL description="A fast, strict, nf-core-style sample sheet validator"

# Install samtools and bcftools for BAM/VCF validation (optional but recommended)
RUN apt-get update && apt-get install -y --no-install-recommends \
    samtools \
    bcftools \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN useradd -m -u 1000 samplesheriff

# Copy and install the wheel from builder
COPY --from=builder /build/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm /tmp/*.whl

# Switch to non-root user
USER samplesheriff

# Set working directory
WORKDIR /data

# Default entrypoint
ENTRYPOINT ["samplesheriff"]
CMD ["--help"]
