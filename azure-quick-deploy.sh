#!/bin/bash

# Script de despliegue rápido para Azure con MongoDB Atlas
# Uso: ./azure-quick-deploy.sh

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Video Profile Extractor - Azure Deployment${NC}"
echo "================================================"

# Variables (personaliza estas)
RESOURCE_GROUP="video-profile-rg"
LOCATION="eastus"
ACR_NAME="videoprofileacr"  # Debe ser único globalmente
APP_SERVICE_PLAN="video-profile-plan"
WEB_APP_NAME="video-profile-api"  # Debe ser único globalmente
IMAGE_NAME="video-profile-extractor"

# Solicitar MongoDB Atlas connection string
echo -e "${YELLOW}📝 Ingresa tu MongoDB Atlas connection string:${NC}"
read -p "MongoDB URI: " MONGODB_URI

# Solicitar API Keys (opcional)
echo -e "${YELLOW}📝 Ingresa tus API Keys (presiona Enter para omitir):${NC}"
read -p "GROQ_API_KEY: " GROQ_KEY
read -p "GEMINI_API_KEY: " GEMINI_KEY
read -p "HUGGINGFACE_API_KEY: " HF_KEY
read -p "OPENROUTER_API_KEY: " OR_KEY

# Verificar Azure CLI
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI no está instalado${NC}"
    echo "Instala desde: https://docs.microsoft.com/cli/azure/install-azure-cli"
    exit 1
fi

echo -e "${GREEN}✓ Azure CLI encontrado${NC}"

# Login
echo -e "${YELLOW}📝 Iniciando sesión en Azure...${NC}"
az login

# Crear Resource Group
echo -e "${YELLOW}📦 Creando Resource Group...${NC}"
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

# Crear Azure Container Registry
echo -e "${YELLOW}🐳 Creando Azure Container Registry...${NC}"
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic \
  --admin-enabled true

# Login en ACR
echo -e "${YELLOW}🔐 Login en ACR...${NC}"
az acr login --name $ACR_NAME

# Build y Push imagen
echo -e "${YELLOW}🏗️  Building y pushing imagen Docker...${NC}"
az acr build \
  --registry $ACR_NAME \
  --image $IMAGE_NAME:latest \
  --file Dockerfile .

# Crear App Service Plan
echo -e "${YELLOW}📋 Creando App Service Plan...${NC}"
az appservice plan create \
  --name $APP_SERVICE_PLAN \
  --resource-group $RESOURCE_GROUP \
  --is-linux \
  --sku B1

# Obtener credenciales ACR
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username --output tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value --output tsv)

# Crear Web App
echo -e "${YELLOW}🌐 Creando Web App...${NC}"
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --name $WEB_APP_NAME \
  --deployment-container-image-name $ACR_NAME.azurecr.io/$IMAGE_NAME:latest

# Configurar container
az webapp config container set \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --docker-custom-image-name $ACR_NAME.azurecr.io/$IMAGE_NAME:latest \
  --docker-registry-server-url https://$ACR_NAME.azurecr.io \
  --docker-registry-server-user $ACR_USERNAME \
  --docker-registry-server-password $ACR_PASSWORD

# Configurar variables de entorno
echo -e "${YELLOW}⚙️  Configurando variables de entorno...${NC}"

SETTINGS="PORT=9000 WEBSITES_PORT=9000 MONGODB_URI=\"$MONGODB_URI\" MONGODB_DATABASE=video_profile_extractor"

if [ ! -z "$GROQ_KEY" ]; then
  SETTINGS="$SETTINGS GROQ_API_KEY=\"$GROQ_KEY\""
fi

if [ ! -z "$GEMINI_KEY" ]; then
  SETTINGS="$SETTINGS GEMINI_API_KEY=\"$GEMINI_KEY\""
fi

if [ ! -z "$HF_KEY" ]; then
  SETTINGS="$SETTINGS HUGGINGFACE_API_KEY=\"$HF_KEY\""
fi

if [ ! -z "$OR_KEY" ]; then
  SETTINGS="$SETTINGS OPENROUTER_API_KEY=\"$OR_KEY\""
fi

az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --settings $SETTINGS

# Habilitar logs
az webapp log config \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --docker-container-logging filesystem

# Habilitar HTTPS only
az webapp update \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --https-only true

# Obtener URL
APP_URL=$(az webapp show \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query defaultHostName \
  --output tsv)

echo ""
echo -e "${GREEN}✅ ¡Despliegue completado!${NC}"
echo "================================================"
echo -e "🌐 URL: ${GREEN}https://$APP_URL${NC}"
echo -e "📊 Health Check: ${GREEN}https://$APP_URL/health${NC}"
echo ""
echo -e "${YELLOW}📝 Comandos útiles:${NC}"
echo ""
echo "# Ver logs en tiempo real:"
echo "az webapp log tail --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP"
echo ""
echo "# Reiniciar app:"
echo "az webapp restart --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP"
echo ""
echo "# Actualizar imagen:"
echo "az acr build --registry $ACR_NAME --image $IMAGE_NAME:latest --file Dockerfile ."
echo "az webapp restart --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP"
echo ""
echo -e "${GREEN}🎉 ¡Listo para usar!${NC}"
