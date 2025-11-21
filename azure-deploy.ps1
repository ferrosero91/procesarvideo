# Script de despliegue para Azure (PowerShell)
# Uso: .\azure-deploy.ps1

$ErrorActionPreference = "Stop"

Write-Host "🚀 Video Profile Extractor - Azure Deployment" -ForegroundColor Green
Write-Host "================================================"

# Variables (personaliza estas)
$RESOURCE_GROUP = "video-profile-rg"
$LOCATION = "eastus"
$ACR_NAME = "videoprofileacr"  # Debe ser único globalmente
$APP_SERVICE_PLAN = "video-profile-plan"
$WEB_APP_NAME = "video-profile-api"  # Debe ser único globalmente
$IMAGE_NAME = "video-profile-extractor"

# Solicitar MongoDB Atlas connection string
Write-Host "📝 Ingresa tu MongoDB Atlas connection string:" -ForegroundColor Yellow
$MONGODB_URI = Read-Host "MongoDB URI"

# Solicitar API Keys (opcional)
Write-Host "📝 Ingresa tus API Keys (presiona Enter para omitir):" -ForegroundColor Yellow
$GROQ_KEY = Read-Host "GROQ_API_KEY"
$GEMINI_KEY = Read-Host "GEMINI_API_KEY"
$HF_KEY = Read-Host "HUGGINGFACE_API_KEY"
$OR_KEY = Read-Host "OPENROUTER_API_KEY"

# Verificar Azure CLI
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Azure CLI no está instalado" -ForegroundColor Red
    Write-Host "Instala desde: https://aka.ms/installazurecliwindows"
    exit 1
}

Write-Host "✓ Azure CLI encontrado" -ForegroundColor Green

# Login
Write-Host "📝 Iniciando sesión en Azure..." -ForegroundColor Yellow
az login

# Crear Resource Group
Write-Host "📦 Creando Resource Group..." -ForegroundColor Yellow
az group create --name $RESOURCE_GROUP --location $LOCATION

# Crear Azure Container Registry
Write-Host "🐳 Creando Azure Container Registry..." -ForegroundColor Yellow
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic --admin-enabled true

# Login en ACR
Write-Host "🔐 Login en ACR..." -ForegroundColor Yellow
az acr login --name $ACR_NAME

# Build y Push imagen
Write-Host "🏗️  Building y pushing imagen Docker..." -ForegroundColor Yellow
az acr build --registry $ACR_NAME --image "${IMAGE_NAME}:latest" --file Dockerfile .

# Crear App Service Plan
Write-Host "📋 Creando App Service Plan..." -ForegroundColor Yellow
az appservice plan create --name $APP_SERVICE_PLAN --resource-group $RESOURCE_GROUP --is-linux --sku B1

# Obtener credenciales ACR
$ACR_USERNAME = az acr credential show --name $ACR_NAME --query username --output tsv
$ACR_PASSWORD = az acr credential show --name $ACR_NAME --query "passwords[0].value" --output tsv

# Crear Web App
Write-Host "🌐 Creando Web App..." -ForegroundColor Yellow
az webapp create --resource-group $RESOURCE_GROUP --plan $APP_SERVICE_PLAN --name $WEB_APP_NAME --deployment-container-image-name "${ACR_NAME}.azurecr.io/${IMAGE_NAME}:latest"

# Configurar container
az webapp config container set --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP --docker-custom-image-name "${ACR_NAME}.azurecr.io/${IMAGE_NAME}:latest" --docker-registry-server-url "https://${ACR_NAME}.azurecr.io" --docker-registry-server-user $ACR_USERNAME --docker-registry-server-password $ACR_PASSWORD

# Configurar variables de entorno
Write-Host "⚙️  Configurando variables de entorno..." -ForegroundColor Yellow

$settings = @(
    "PORT=9000"
    "WEBSITES_PORT=9000"
    "MONGODB_URI=$MONGODB_URI"
    "MONGODB_DATABASE=video_profile_extractor"
)

if ($GROQ_KEY) { $settings += "GROQ_API_KEY=$GROQ_KEY" }
if ($GEMINI_KEY) { $settings += "GEMINI_API_KEY=$GEMINI_KEY" }
if ($HF_KEY) { $settings += "HUGGINGFACE_API_KEY=$HF_KEY" }
if ($OR_KEY) { $settings += "OPENROUTER_API_KEY=$OR_KEY" }

az webapp config appsettings set --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME --settings $settings

# Habilitar logs
az webapp log config --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP --docker-container-logging filesystem

# Habilitar HTTPS only
az webapp update --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME --https-only true

# Obtener URL
$APP_URL = az webapp show --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP --query defaultHostName --output tsv

Write-Host ""
Write-Host "✅ ¡Despliegue completado!" -ForegroundColor Green
Write-Host "================================================"
Write-Host "🌐 URL: https://$APP_URL" -ForegroundColor Green
Write-Host "📊 Health Check: https://$APP_URL/health" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Comandos útiles:" -ForegroundColor Yellow
Write-Host ""
Write-Host "# Ver logs en tiempo real:"
Write-Host "az webapp log tail --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP"
Write-Host ""
Write-Host "# Reiniciar app:"
Write-Host "az webapp restart --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP"
Write-Host ""
Write-Host "# Actualizar imagen:"
Write-Host "az acr build --registry $ACR_NAME --image ${IMAGE_NAME}:latest --file Dockerfile ."
Write-Host "az webapp restart --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP"
Write-Host ""
Write-Host "🎉 ¡Listo para usar!" -ForegroundColor Green
