# Используем официальный образ как базовый
FROM baserow/baserow:latest

# Устанавливаем зависимости перед копированием файлов
WORKDIR /baserow/web-frontend
RUN npm config set registry https://registry.npmjs.org/ && \
    npm config set fetch-retry-maxtimeout 600000 && \
    npm config set fetch-retry-mintimeout 10000 && \
    npm install --save-dev @nuxtjs/stylelint-module --legacy-peer-deps

# Копируем наши модифицированные файлы
COPY premium/backend/src/baserow_premium/license/handler.py /baserow/backend/src/baserow_premium/license/handler.py
COPY premium/web-frontend/modules/baserow_premium/components/PremiumModal.vue /baserow/web-frontend/modules/baserow_premium/components/PremiumModal.vue
COPY premium/web-frontend/modules/baserow_premium/components/views/grid/fields/GridViewFieldAIGenerateValuesContextItem.vue /baserow/web-frontend/modules/baserow_premium/components/views/grid/fields/GridViewFieldAIGenerateValuesContextItem.vue
COPY premium/web-frontend/modules/baserow_premium/fieldTypes.js /baserow/web-frontend/modules/baserow_premium/fieldTypes.js
COPY premium/web-frontend/modules/baserow_premium/mixins/fieldAI.js /baserow/web-frontend/modules/baserow_premium/mixins/fieldAI.js

# Собираем frontend
RUN npm run build

# Очищаем dev-зависимости после сборки
RUN npm prune --production

# Перезапускаем сервисы
RUN supervisorctl restart all
