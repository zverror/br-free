#!/bin/bash

# Pull the latest Baserow image
docker pull baserow/baserow:latest

# Create a temporary container
CONTAINER_ID=$(docker create baserow/baserow:latest)

# Copy our modified files into the container
docker cp premium/backend/src/baserow_premium/license/handler.py $CONTAINER_ID:/baserow/backend/src/baserow_premium/license/handler.py
docker cp premium/web-frontend/modules/baserow_premium/components/PremiumModal.vue $CONTAINER_ID:/baserow/web-frontend/modules/baserow_premium/components/PremiumModal.vue
docker cp premium/web-frontend/modules/baserow_premium/components/views/grid/fields/GridViewFieldAIGenerateValuesContextItem.vue $CONTAINER_ID:/baserow/web-frontend/modules/baserow_premium/components/views/grid/fields/GridViewFieldAIGenerateValuesContextItem.vue
docker cp premium/web-frontend/modules/baserow_premium/fieldTypes.js $CONTAINER_ID:/baserow/web-frontend/modules/baserow_premium/fieldTypes.js
docker cp premium/web-frontend/modules/baserow_premium/mixins/fieldAI.js $CONTAINER_ID:/baserow/web-frontend/modules/baserow_premium/mixins/fieldAI.js

# Commit the container to a new image
docker commit $CONTAINER_ID baserow-free:latest

# Remove the temporary container
docker rm $CONTAINER_ID

# Create and start the container
docker run -d \
  --name baserow-free \
  -p 8280:80 \
  -p 8243:443 \
  -v baserow_data:/baserow/data \
  -e BASEROW_PUBLIC_URL=http://localhost:8280 \
  baserow-free:latest
