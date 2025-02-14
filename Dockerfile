FROM baserow/baserow:1.22.2

COPY premium/backend /baserow/data/plugins/premium/backend

ENV BASEROW_ENABLE_ALL_PREMIUM_FEATURES=true
