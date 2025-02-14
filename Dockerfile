FROM python:3.9-slim as builder

WORKDIR /baserow
COPY premium/backend /baserow/data/plugins/premium/backend

RUN pip install --upgrade pip && \
    pip install build && \
    cd /baserow/data/plugins/premium/backend && \
    python -m build

FROM baserow/baserow:1.22.2

COPY --from=builder /baserow/data/plugins/premium/backend/dist/*.whl /baserow/data/plugins/premium/backend/dist/

ENV BASEROW_ENABLE_ALL_PREMIUM_FEATURES=true
