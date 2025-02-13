# Используем официальный образ как базовый
FROM baserow/baserow:latest

# Копируем наши модифицированные файлы
COPY premium/backend/src/baserow_premium/license/handler.py /baserow/backend/src/baserow_premium/license/handler.py
COPY premium/web-frontend/modules/baserow_premium/components/PremiumModal.vue /baserow/web-frontend/modules/baserow_premium/components/PremiumModal.vue
COPY premium/web-frontend/modules/baserow_premium/components/views/grid/fields/GridViewFieldAIGenerateValuesContextItem.vue /baserow/web-frontend/modules/baserow_premium/components/views/grid/fields/GridViewFieldAIGenerateValuesContextItem.vue
COPY premium/web-frontend/modules/baserow_premium/fieldTypes.js /baserow/web-frontend/modules/baserow_premium/fieldTypes.js
COPY premium/web-frontend/modules/baserow_premium/mixins/fieldAI.js /baserow/web-frontend/modules/baserow_premium/mixins/fieldAI.js

# Устанавливаем необходимые dev-зависимости и собираем frontend
RUN cd /baserow/web-frontend && \
    npm install --save-dev @nuxtjs/stylelint-module --legacy-peer-deps && \
    npm run build

# Очищаем dev-зависимости после сборки
RUN cd /baserow/web-frontend && \
    npm prune --production

# Перезапускаем сервисы
RUN supervisorctl restart all
