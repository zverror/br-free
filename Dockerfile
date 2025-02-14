FROM baserow/baserow:1.22.2 as builder

WORKDIR /baserow
COPY premium/backend /baserow/premium/backend

RUN cd /baserow/premium/backend && \
    python -m pip install --upgrade pip && \
    python -m pip install build && \
    python -m build

FROM baserow/baserow:1.22.2

COPY --from=builder /baserow/premium/backend/dist/*.whl /baserow/data/plugins/premium/backend.whl
RUN python -m pip install /baserow/data/plugins/premium/backend.whl

ENV BASEROW_ENABLE_ALL_PREMIUM_FEATURES=true
