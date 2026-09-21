FROM ghcr.io/astral-sh/uv:python3.13-bookworm@sha256:47965cdc9d53a515f68f78241161c901e70051ce428f12e791bd7fe19f6a631a

COPY requirements.txt /opt/runtime/requirements.txt
RUN uv pip install --system --require-hashes -r /opt/runtime/requirements.txt
WORKDIR /workspace
