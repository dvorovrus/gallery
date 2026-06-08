#!/bin/bash

# Gallery Application Deployment Script
# Скрипт для деплоя приложения Gallery на сервер

set -e  # Exit on error

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Конфигурация
PROJECT_NAME="gallery"
SERVER_USER="ai-bot"
SERVER_HOST="149.202.61.227"
SSH_KEY="$HOME/.ssh/id_ed25519"
DEPLOY_DIR="/opt/${PROJECT_NAME}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Gallery Application Deployment${NC}"
echo -e "${GREEN}========================================${NC}"

# Проверка наличия .env файла
if [ ! -f ".env" ]; then
    echo -e "${RED}Ошибка: Файл .env не найден!${NC}"
    echo -e "${YELLOW}Создайте файл .env на основе .env.example${NC}"
    echo -e "${YELLOW}cp .env.example .env${NC}"
    echo -e "${YELLOW}И заполните все необходимые переменные${NC}"
    exit 1
fi

if [ ! -f "backend/.env.prod" ]; then
    echo -e "${RED}Ошибка: Файл backend/.env.prod не найден!${NC}"
    echo -e "${YELLOW}Создайте файл на основе backend/.env.prod.example${NC}"
    echo -e "${YELLOW}cp backend/.env.prod.example backend/.env.prod${NC}"
    echo -e "${YELLOW}И заполните все необходимые переменные${NC}"
    exit 1
fi

# Функция для выполнения команд на сервере
ssh_exec() {
    ssh -i "$SSH_KEY" "${SERVER_USER}@${SERVER_HOST}" "$@"
}

echo -e "${YELLOW}[1/6] Проверка подключения к серверу...${NC}"
if ! ssh_exec "echo 'OK'" > /dev/null 2>&1; then
    echo -e "${RED}Ошибка: Не удалось подключиться к серверу${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Подключение установлено${NC}"

echo -e "${YELLOW}[2/6] Создание директории на сервере...${NC}"
ssh_exec "sudo mkdir -p ${DEPLOY_DIR} && sudo chown ${SERVER_USER}:${SERVER_USER} ${DEPLOY_DIR}"
echo -e "${GREEN}✓ Директория создана: ${DEPLOY_DIR}${NC}"

echo -e "${YELLOW}[3/6] Копирование файлов на сервер...${NC}"
rsync -avz --delete \
    --exclude 'node_modules' \
    --exclude 'venv' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude 'dist' \
    --exclude 'build' \
    --exclude '.git' \
    --exclude 'gallery.db' \
    --exclude 'uploads' \
    --exclude 'token.json' \
    --exclude 'oauth_credentials.json' \
    -e "ssh -i ${SSH_KEY}" \
    ./ "${SERVER_USER}@${SERVER_HOST}:${DEPLOY_DIR}/"
echo -e "${GREEN}✓ Файлы скопированы${NC}"

echo -e "${YELLOW}[4/6] Сборка Docker образов...${NC}"
ssh_exec "cd ${DEPLOY_DIR} && docker compose build"
echo -e "${GREEN}✓ Образы собраны${NC}"

echo -e "${YELLOW}[5/6] Запуск контейнеров...${NC}"
ssh_exec "cd ${DEPLOY_DIR} && docker compose up -d"
echo -e "${GREEN}✓ Контейнеры запущены${NC}"

echo -e "${YELLOW}[6/6] Применение миграций базы данных...${NC}"
sleep 5  # Ждем, пока контейнеры полностью запустятся
ssh_exec "cd ${DEPLOY_DIR} && docker compose exec -T backend alembic upgrade head" || echo -e "${YELLOW}⚠ Миграции могли не примениться. Проверьте вручную.${NC}"
echo -e "${GREEN}✓ Миграции применены${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Деплой завершен успешно!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Проверка статуса:${NC}"
ssh_exec "cd ${DEPLOY_DIR} && docker compose ps"

echo ""
echo -e "${YELLOW}Логи можно посмотреть командой:${NC}"
echo -e "ssh -i ${SSH_KEY} ${SERVER_USER}@${SERVER_HOST} 'cd ${DEPLOY_DIR} && docker compose logs -f'"

echo ""
echo -e "${GREEN}Приложение доступно по адресу из переменной DOMAIN в .env${NC}"
