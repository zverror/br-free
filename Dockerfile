# Используем официальный образ как базовый
FROM baserow/baserow:latest

# Копируем наши модифицированные файлы
COPY premium/backend/src/baserow_premium/license/handler.py /baserow/backend/src/baserow_premium/license/handler.py
COPY premium/web-frontend/modules/baserow_premium/components/PremiumModal.vue /baserow/web-frontend/modules/baserow_premium/components/PremiumModal.vue
COPY premium/web-frontend/modules/baserow_premium/components/views/grid/fields/GridViewFieldAIGenerateValuesContextItem.vue /baserow/web-frontend/modules/baserow_premium/components/views/grid/fields/GridViewFieldAIGenerateValuesContextItem.vue
COPY premium/web-frontend/modules/baserow_premium/fieldTypes.js /baserow/web-frontend/modules/baserow_premium/fieldTypes.js
COPY premium/web-frontend/modules/baserow_premium/mixins/fieldAI.js /baserow/web-frontend/modules/baserow_premium/mixins/fieldAI.js

# Пересобираем frontend
RUN cd /baserow/web-frontend && \
    npm run build

# Перезапускаем сервисы
RUN supervisorctl restart all
