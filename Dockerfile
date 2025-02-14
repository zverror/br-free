FROM baserow/baserow:1.22.2

COPY premium/backend/src/baserow_premium /baserow/plugins/premium/backend/src/baserow_premium

ENV BASEROW_ENABLE_ALL_PREMIUM_FEATURES=true
ENV BASEROW_PLUGIN_DIR=/baserow/plugins
