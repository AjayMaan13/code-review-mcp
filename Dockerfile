# Use the official Python 3.13 slim image as the base.
# "slim" strips out things like compilers and docs — smaller image, faster to pull.
FROM python:3.13-slim

# Install uv — the same package manager used locally.
# We use the official install script piped into sh.
# `--no-cache` keeps the image smaller by not storing the apt cache after install.
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && curl -Ls https://astral.sh/uv/install.sh | sh \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Add uv to PATH so we can call it in subsequent RUN steps.
ENV PATH="/root/.local/bin:$PATH"

# Set the working directory inside the container.
# All subsequent COPY and RUN commands operate relative to this path.
WORKDIR /app

# Copy dependency files first — before the source code.
# Docker caches each layer. If these files haven't changed, Docker skips
# reinstalling dependencies on the next build even if source files changed.
COPY pyproject.toml uv.lock ./

# Install dependencies from the lockfile into the system Python (not a .venv).
# --frozen: don't update the lockfile, use it exactly as-is.
# --no-install-project: only install dependencies, not the project itself.
RUN uv pip install --system --no-cache -r pyproject.toml

# Copy the source code into the container.
# This comes after dependency install so code changes don't bust the dep cache.
COPY server.py github_client.py tools.py resources.py prompts.py config.py ./

# Tell Docker this container communicates over stdio, not a network port.
# MCP stdio transport reads from stdin and writes to stdout —
# no port needs to be opened or exposed.
# CMD is the default command run when the container starts.
CMD ["python", "server.py"]
