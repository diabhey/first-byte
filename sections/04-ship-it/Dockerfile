# This is an example Dockerfile that builds a minimal container for running LK Agents
# For more information on the build process, see https://docs.livekit.io/agents/ops/deployment/builds/
# syntax=docker/dockerfile:1

# Use Python 3.13 on Debian Trixie (glibc 2.38) so wheels that require
# manylinux_2_38+ install cleanly. Notably, inferedge-moss-core (the binary
# behind the `moss` package) only ships manylinux_2_38_x86_64 wheels for
# Linux x86_64, which the older bookworm-slim base (glibc 2.36) cannot use.
# uv is installed by copying its statically-linked binary from astral's image.
ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION}-slim-trixie AS base
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

# --- Build stage ---
# Install dependencies, build native extensions, and prepare the application
FROM base AS build

# Install build dependencies required for Python packages with native extensions
# gcc: C compiler needed for building Python packages with C extensions
# g++: C++ compiler needed for building Python packages with C++ extensions
# python3-dev: Python development headers needed for compilation
# We clean up the apt cache after installation to keep the image size down
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
  && rm -rf /var/lib/apt/lists/*

# Create a new directory for our application code
# And set it as the working directory
WORKDIR /app

# Copy just the dependency files first, for more efficient layer caching
COPY pyproject.toml uv.lock ./
RUN mkdir -p src

# Install Python dependencies using UV's lock file
# --locked ensures we use exact versions from uv.lock for reproducible builds
# This creates a virtual environment and installs all dependencies
# Ensure your uv.lock file is checked in for consistency across environments
RUN uv sync --locked

# Copy all remaining application files into the container
# This includes source code, configuration files, and dependency specifications
# (Excludes files specified in .dockerignore)
COPY . .

# Pre-download any ML models or files the agent needs
# This ensures the container is ready to run immediately without downloading
# dependencies at runtime, which improves startup time and reliability
RUN uv run "agent.py" download-files

# --- Production stage ---
# Build tools (gcc, g++, python3-dev) are not included in the final image
FROM base

# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/build/building/best-practices/#user
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/app" \
    --shell "/sbin/nologin" \
    --uid "${UID}" \
    appuser

WORKDIR /app

# Copy the application and virtual environment with correct ownership in a single layer
# This avoids expensive recursive chown and excludes build tools from the final image
COPY --from=build --chown=appuser:appuser /app /app

# Switch to the non-privileged user for all subsequent operations
# This improves security by not running as root
USER appuser

# Run the application using UV
# UV will activate the virtual environment and run the agent.
# The "start" command tells the worker to connect to LiveKit and begin waiting for jobs.
CMD ["uv", "run", "agent.py", "start"]
