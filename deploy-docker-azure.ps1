# Script para desplegar con Docker en Azure

$RESOURCE_GROUP = "Pruebas"
$WEB_APP_NAME = "procesarvideo"
$ACR_NAME = "procesarvideoregistry"
$IMAGE_NAME = "video-profile-api"
$LOCATION = "canadacentral"

Write-Host "Desplegando con Docker Container..." -ForegroundColor Yellow

# Refrescar PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Crear Azure Container Registry
Write-Host "Creando Azure Container Registry..." -ForegroundColor Yellow
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic --location $LOCATION --admin-enabled true

# Login en ACR
Write-Host "Login en ACR..." -ForegroundColor Yellow
az acr login --name $ACR_NAME

# Build y push imagen
Write-Host "Building y pushing imagen Docker..." -ForegroundColor Yellow
az acr build --registry $ACR_NAME --image "${IMAGE_NAME}:latest" --file Dockerfile .

# Obtener credenciales
$ACR_USERNAME = az acr credential show --name $ACR_NAME --query username --output tsv
$ACR_PASSWORD = az acr credential show --name $ACR_NAME --query "passwords[0].value" --output tsv
$ACR_LOGIN_SERVER = az acr show --name $ACR_NAME --query loginServer --output tsv

# Configurar Web App para usar Docker
Write-Host "Configurando Web App para Docker..." -ForegroundColor Yellow
az webapp config container set `
  --name $WEB_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --docker-custom-image-name "${ACR_LOGIN_SERVER}/${IMAGE_NAME}:latest" `
  --docker-registry-server-url "https://${ACR_LOGIN_SERVER}" `
  --docker-registry-server-user $ACR_USERNAME `
  --docker-registry-server-password $ACR_PASSWORD

# Reiniciar
Write-Host "Reiniciando aplicacion..." -ForegroundColor Yellow
az webapp restart --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP

Write-Host ""
Write-Host "Despliegue completado!" -ForegroundColor Green
Write-Host "URL: https://procesarvideo.azurewebsites.net/health" -ForegroundColor Cyan
Write-Host "Espera 2-3 minutos para que el container inicie" -ForegroundColor Yellow
