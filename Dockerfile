FROM python:3.11-slim as builder

# Копируем premium плагин
COPY . /baserow/premium/

# Устанавливаем зависимости для сборки
RUN cd /baserow/premium/backend && \
    pip install build && \
    python -m build

FROM baserow/baserow:1.22.2

# Копируем собранный плагин
COPY --from=builder /baserow/premium /baserow/data/plugins/premium/

# Включаем premium функции
ENV BASEROW_ENABLE_ALL_PREMIUM_FEATURES=true
