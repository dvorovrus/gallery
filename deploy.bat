@echo off
REM Gallery Application Deployment Script for Windows
REM Скрипт для деплоя приложения Gallery на сервер (Windows версия)

setlocal enabledelayedexpansion

REM Конфигурация
set PROJECT_NAME=gallery
set SERVER_USER=ai-bot
set SERVER_HOST=149.202.61.227
set SSH_KEY=%USERPROFILE%\.ssh\id_ed25519
set DEPLOY_DIR=/opt/%PROJECT_NAME%

echo ========================================
echo Gallery Application Deployment
echo ========================================
echo.

REM Проверка наличия .env файла
if not exist ".env" (
    echo [ERROR] Файл .env не найден!
    echo Создайте файл .env на основе .env.example
    echo   copy .env.example .env
    echo И заполните все необходимые переменные
    exit /b 1
)

if not exist "backend\.env.prod" (
    echo [ERROR] Файл backend\.env.prod не найден!
    echo Создайте файл на основе backend\.env.prod.example
    echo   copy backend\.env.prod.example backend\.env.prod
    echo И заполните все необходимые переменные
    exit /b 1
)

echo [1/6] Проверка подключения к серверу...
ssh -i "%SSH_KEY%" %SERVER_USER%@%SERVER_HOST% "echo OK" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Не удалось подключиться к серверу
    exit /b 1
)
echo [OK] Подключение установлено
echo.

echo [2/6] Создание директории на сервере...
ssh -i "%SSH_KEY%" %SERVER_USER%@%SERVER_HOST% "sudo mkdir -p %DEPLOY_DIR% && sudo chown %SERVER_USER%:%SERVER_USER% %DEPLOY_DIR%"
echo [OK] Директория создана: %DEPLOY_DIR%
echo.

echo [3/6] Копирование файлов на сервер...
rsync -avz --delete --exclude "node_modules" --exclude "venv" --exclude "__pycache__" --exclude "*.pyc" --exclude "dist" --exclude "build" --exclude ".git" --exclude "gallery.db" --exclude "uploads" --exclude "token.json" --exclude "oauth_credentials.json" -e "ssh -i %SSH_KEY%" ./ %SERVER_USER%@%SERVER_HOST%:%DEPLOY_DIR%/
if errorlevel 1 (
    echo [ERROR] Ошибка при копировании файлов
    exit /b 1
)
echo [OK] Файлы скопированы
echo.

echo [4/6] Сборка Docker образов...
ssh -i "%SSH_KEY%" %SERVER_USER%@%SERVER_HOST% "cd %DEPLOY_DIR% && docker compose build"
if errorlevel 1 (
    echo [ERROR] Ошибка при сборке образов
    exit /b 1
)
echo [OK] Образы собраны
echo.

echo [5/6] Запуск контейнеров...
ssh -i "%SSH_KEY%" %SERVER_USER%@%SERVER_HOST% "cd %DEPLOY_DIR% && docker compose up -d"
if errorlevel 1 (
    echo [ERROR] Ошибка при запуске контейнеров
    exit /b 1
)
echo [OK] Контейнеры запущены
echo.

echo [6/6] Применение миграций базы данных...
timeout /t 5 /nobreak >nul
ssh -i "%SSH_KEY%" %SERVER_USER%@%SERVER_HOST% "cd %DEPLOY_DIR% && docker compose exec -T backend alembic upgrade head"
if errorlevel 1 (
    echo [WARNING] Миграции могли не примениться. Проверьте вручную.
) else (
    echo [OK] Миграции применены
)
echo.

echo ========================================
echo Деплой завершен успешно!
echo ========================================
echo.

echo Проверка статуса:
ssh -i "%SSH_KEY%" %SERVER_USER%@%SERVER_HOST% "cd %DEPLOY_DIR% && docker compose ps"

echo.
echo Логи можно посмотреть командой:
echo ssh -i "%SSH_KEY%" %SERVER_USER%@%SERVER_HOST% "cd %DEPLOY_DIR% && docker compose logs -f"
echo.
echo Приложение доступно по адресу из переменной DOMAIN в .env

endlocal
