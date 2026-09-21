FROM ghcr.io/astral-sh/uv:python3.13-bookworm

COPY requirements.txt /opt/runtime/requirements.txt
RUN uv pip install --system --require-hashes -r /opt/runtime/requirements.txt
WORKDIR /workspace
