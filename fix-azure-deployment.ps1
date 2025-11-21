# Script para corregir el despliegue de Azure
# Cambia de Python Code a Docker Container

$RESOURCE_GROUP = Read-Host "Ingresa el nombre de tu Resource Group"
$WEB_APP_NAME = "procesarvideo"
$ACR_NAME = Read-Host "Ingresa el nombre de tu Azure Container Registry (si lo creaste)"
$IMAGE_NAME = "video-profile-extractor"

Write-Host "🔧 Corrigiendo configuración de Azure App Service..." -ForegroundColor Yellow

# Obtener credenciales de ACR
$ACR_USERNAME = az acr credential show --name $ACR_NAME --query username --output tsv
$ACR_PASSWORD = az acr credential show --name $ACR_NAME --query "passwords[0].value" --output tsv

# Configurar para usar Docker Container
Write-Host "📦 Configurando Docker Container..." -ForegroundColor Yellow
az webapp config container set `
  --name $WEB_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --docker-custom-image-name "${ACR_NAME}.azurecr.io/${IMAGE_NAME}:latest" `
  --docker-registry-server-url "https://${ACR_NAME}.azurecr.io" `
  --docker-registry-server-user $ACR_USERNAME `
  --docker-registry-server-password $ACR_PASSWORD

# Aplicar configuraciones desde el archivo JSON
Write-Host "⚙️  Aplicando variables de entorno..." -ForegroundColor Yellow
az webapp config appsettings set `
  --name $WEB_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --settings "@azure-app-settings.json"

# Reiniciar la app
Write-Host "🔄 Reiniciando aplicación..." -ForegroundColor Yellow
az webapp restart --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP

Write-Host ""
Write-Host "✅ Configuración corregida!" -ForegroundColor Green
Write-Host "Espera 1-2 minutos y verifica: https://${WEB_APP_NAME}.azurewebsites.net/health"
