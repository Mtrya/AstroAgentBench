FROM ghcr.io/astral-sh/uv:python3.13-trixie-slim@sha256:6ff812e34a0e14b4b8bc9ddf25e77b3e16bac6e0c4d9b67641f40366fa382d4c

COPY requirements.txt /opt/runtime/requirements.txt
RUN uv pip install --system --require-hashes -r /opt/runtime/requirements.txt
WORKDIR /workspace
