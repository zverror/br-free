FROM baserow/baserow:1.22.2

COPY . /baserow/data/plugins/premium/
ENV BASEROW_ENABLE_ALL_PREMIUM_FEATURES=true
