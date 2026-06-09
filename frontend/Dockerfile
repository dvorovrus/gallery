# Multi-stage build для frontend
FROM node:20-alpine as builder

WORKDIR /app

# Копирование package files
COPY package*.json ./

# Установка зависимостей (включая dev для сборки)
RUN npm ci

# Копирование исходного кода
COPY . .

ARG VITE_API_URL=""
ENV VITE_API_URL=$VITE_API_URL

# Сборка приложения
RUN npm run build

# Production stage с nginx
FROM nginx:alpine

# Копирование собранного приложения
COPY --from=builder /app/dist /usr/share/nginx/html

# Копирование конфигурации nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose порт
EXPOSE 80

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
