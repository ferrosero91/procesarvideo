# Script para configurar Azure App Service con startup script y variables de entorno

$RESOURCE_GROUP = "procesarvideo-azurewebsites-net"
$WEB_APP_NAME = "procesarvideo"

Write-Host "🔧 Configurando Azure App Service..." -ForegroundColor Yellow

# Instalar Azure CLI si no está instalado
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Host "📦 Instalando Azure CLI..." -ForegroundColor Yellow
    winget install Microsoft.AzureCLI
    Write-Host "⚠️  Cierra y abre una nueva terminal, luego ejecuta este script nuevamente" -ForegroundColor Red
    exit
}

# Login en Azure
Write-Host "🔐 Iniciando sesión en Azure..." -ForegroundColor Yellow
az login

# Configurar startup command
Write-Host "⚙️  Configurando startup script..." -ForegroundColor Yellow
az webapp config set `
  --name $WEB_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --startup-file "startup.sh"

# Aplicar variables de entorno desde el archivo JSON
Write-Host "📝 Aplicando variables de entorno..." -ForegroundColor Yellow
az webapp config appsettings set `
  --name $WEB_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --settings `@azure-app-settings.json`

# Reiniciar la aplicación
Write-Host "🔄 Reiniciando aplicación..." -ForegroundColor Yellow
az webapp restart `
  --name $WEB_APP_NAME `
  --resource-group $RESOURCE_GROUP

Write-Host ""
Write-Host "✅ Configuración completada!" -ForegroundColor Green
Write-Host "🌐 URL: https://procesarvideo.azurewebsites.net" -ForegroundColor Cyan
Write-Host "📊 Health Check: https://procesarvideo.azurewebsites.net/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "⏳ Espera 2-3 minutos para que la app se reinicie con FFmpeg instalado" -ForegroundColor Yellow
Write-Host ""
Write-Host "📝 Ver logs:" -ForegroundColor Yellow
Write-Host "az webapp log tail --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP"
