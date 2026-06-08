# PowerShell Deploy Script for Gallery Application
# Скрипт деплоя для Windows с использованием PowerShell

$ErrorActionPreference = "Stop"

# Конфигурация
$PROJECT_NAME = "gallery"
$SERVER_USER = "ai-bot"
$SERVER_HOST = "149.202.61.227"
$SSH_KEY = "$env:USERPROFILE\.ssh\id_ed25519"
$DEPLOY_DIR = "/home/$SERVER_USER/$PROJECT_NAME"
$TEMP_ARCHIVE = "gallery-deploy.tar.gz"

Write-Host "========================================" -ForegroundColor Green
Write-Host "Gallery Application Deployment" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Проверка наличия .env файлов
if (-not (Test-Path ".env")) {
    Write-Host "[ERROR] Файл .env не найден!" -ForegroundColor Red
    Write-Host "Создайте файл .env на основе .env.example" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path "backend\.env.prod")) {
    Write-Host "[ERROR] Файл backend\.env.prod не найден!" -ForegroundColor Red
    Write-Host "Создайте файл на основе backend\.env.prod.example" -ForegroundColor Yellow
    exit 1
}

Write-Host "[1/7] Проверка подключения к серверу..." -ForegroundColor Yellow
$testConnection = ssh -i $SSH_KEY "${SERVER_USER}@${SERVER_HOST}" "echo OK" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Не удалось подключиться к серверу" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Подключение установлено" -ForegroundColor Green
Write-Host ""

Write-Host "[2/7] Создание архива проекта..." -ForegroundColor Yellow
# Используем tar (доступен в Windows 10+)
$excludes = @(
    "--exclude=node_modules",
    "--exclude=venv",
    "--exclude=__pycache__",
    "--exclude=*.pyc",
    "--exclude=dist",
    "--exclude=build",
    "--exclude=.git",
    "--exclude=gallery.db",
    "--exclude=uploads",
    "--exclude=token.json",
    "--exclude=oauth_credentials.json",
    "--exclude=$TEMP_ARCHIVE"
)

tar -czf $TEMP_ARCHIVE $excludes .
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Ошибка при создании архива" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Архив создан: $TEMP_ARCHIVE" -ForegroundColor Green
Write-Host ""

Write-Host "[3/7] Создание директории на сервере..." -ForegroundColor Yellow
ssh -i $SSH_KEY "${SERVER_USER}@${SERVER_HOST}" "mkdir -p $DEPLOY_DIR" 2>&1
Write-Host "[OK] Директория готова: $DEPLOY_DIR" -ForegroundColor Green
Write-Host ""

Write-Host "[4/7] Копирование архива на сервер..." -ForegroundColor Yellow
scp -i $SSH_KEY $TEMP_ARCHIVE "${SERVER_USER}@${SERVER_HOST}:${DEPLOY_DIR}/"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Ошибка при копировании архива" -ForegroundColor Red
    Remove-Item $TEMP_ARCHIVE -ErrorAction SilentlyContinue
    exit 1
}
Write-Host "[OK] Архив скопирован" -ForegroundColor Green

# Удаление локального архива
Remove-Item $TEMP_ARCHIVE
Write-Host ""

Write-Host "[5/7] Распаковка архива на сервере..." -ForegroundColor Yellow
ssh -i $SSH_KEY "${SERVER_USER}@${SERVER_HOST}" "cd $DEPLOY_DIR && tar -xzf $TEMP_ARCHIVE && rm $TEMP_ARCHIVE"
Write-Host "[OK] Архив распакован" -ForegroundColor Green
Write-Host ""

Write-Host "[6/7] Сборка и запуск контейнеров..." -ForegroundColor Yellow
ssh -i $SSH_KEY "${SERVER_USER}@${SERVER_HOST}" "cd $DEPLOY_DIR && docker-compose build && docker-compose up -d"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Ошибка при сборке/запуске контейнеров" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Контейнеры запущены" -ForegroundColor Green
Write-Host ""

Write-Host "[7/7] Применение миграций базы данных..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
ssh -i $SSH_KEY "${SERVER_USER}@${SERVER_HOST}" "cd $DEPLOY_DIR && docker-compose exec -T backend alembic upgrade head" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARNING] Миграции могли не примениться. Проверьте вручную." -ForegroundColor Yellow
} else {
    Write-Host "[OK] Миграции применены" -ForegroundColor Green
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "Деплой завершен успешно!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host "Проверка статуса:" -ForegroundColor Yellow
ssh -i $SSH_KEY "${SERVER_USER}@${SERVER_HOST}" "cd $DEPLOY_DIR && docker-compose ps"

Write-Host ""
Write-Host "Логи можно посмотреть командой:" -ForegroundColor Yellow
Write-Host "ssh -i `"$SSH_KEY`" ${SERVER_USER}@${SERVER_HOST} 'cd $DEPLOY_DIR && docker-compose logs -f'" -ForegroundColor Cyan
Write-Host ""
Write-Host "Приложение доступно по адресу: https://gallery.fatbox.org" -ForegroundColor Green
