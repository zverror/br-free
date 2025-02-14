FROM baserow/baserow:1.22.2

COPY premium/backend /baserow/premium/backend

RUN apt-get update && \
    apt-get install -y python3-pip python3-venv && \
    cd /baserow/premium/backend && \
    python3 -m pip install --upgrade pip && \
    python3 -m pip install build && \
    python3 -m build && \
    python3 -m pip install dist/*.whl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV BASEROW_ENABLE_ALL_PREMIUM_FEATURES=true
