# Baserow Premium Free

This repository contains a modified version of Baserow with premium features enabled for all users. It's based on the official Baserow image but includes modifications to remove premium license checks.

## Features Enabled

- AI Prompt functionality
- All premium features are accessible without license checks

## Quick Start

1. Clone this repository:
```bash
git clone https://github.com/YOUR_USERNAME/baserow-premium-free.git
cd baserow-premium-free
```

2. Update the `BASEROW_PUBLIC_URL` in docker-compose.yml to match your domain.

3. Run with Docker Compose:
```bash
docker-compose up -d
```

## Deployment with Coolify

1. Add this repository to your Coolify instance
2. Set the required environment variables:
   - `BASEROW_PUBLIC_URL`: Your public URL
3. Deploy using the provided docker-compose.yml

## Modified Files

The following files have been modified to enable premium features:
- `premium/backend/src/baserow_premium/license/handler.py`
- `premium/web-frontend/modules/baserow_premium/fieldTypes.js`
- `premium/web-frontend/modules/baserow_premium/components/PremiumModal.vue`
- `premium/web-frontend/modules/baserow_premium/components/views/grid/fields/GridViewFieldAIGenerateValuesContextItem.vue`
- `premium/web-frontend/modules/baserow_premium/mixins/fieldAI.js`

## Important Note

This is a modified version of Baserow and should be used for development/testing purposes only. For production use, please consider purchasing a proper Baserow license to support the project.
