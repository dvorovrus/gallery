# Развертывание (Deployment)

## Обзор

В этом руководстве описаны различные способы развертывания приложения Gallery: от простого локального запуска до production-ready развертывания с Docker и облачными платформами.

## Требования к окружению

### Минимальные требования:

**Backend:**
- Python 3.11+
- PostgreSQL 15+
- 512 MB RAM
- 1 CPU core

**Frontend:**
- Node.js 20+
- 256 MB RAM
- 1 CPU core

**Google Drive:**
- Google Cloud Project с включенным Drive API
- Service Account с JSON ключом
- Выделенная папка на Drive

### Рекомендуемые требования (Production):

**Backend:**
- Python 3.11+
- PostgreSQL 15+
- 2 GB RAM
- 2 CPU cores

**Frontend:**
- Nginx для отдачи статики
- 512 MB RAM
- 1 CPU core

**Database:**
- PostgreSQL managed service
- 1 GB RAM
- 10 GB SSD storage

---

## Локальное развертывание

### 1. Клонирование и установка

```bash
# Клонировать репозиторий
git clone <repository-url>
cd gallery

# Backend
cd backend
python -m venv venv

# Активировать venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### 2. Настройка окружения

```bash
# Backend .env
cd backend
cp .env.example .env
# Отредактировать .env с правильными credentials

# Поместить service-account.json в backend/
```

### 3. Настройка базы данных

```bash
# Создать БД
createdb gallery

# Применить миграции
cd backend
alembic upgrade head
```

### 4. Запуск

**Backend (Terminal 1):**
```bash
cd backend

# Активировать venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Запустить сервер
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend (Terminal 2):**
```bash
cd frontend
npm run dev
```

**Открыть:** http://localhost:5173

---

## Production развертывание

### Вариант 1: Отдельные сервисы

#### Frontend на Vercel

```bash
cd frontend

# Build
npm run build

# Deploy
npx vercel --prod

# Environment variables в Vercel:
VITE_API_URL=https://your-backend-domain.com
```

#### Backend на Railway

```bash
cd backend

# Создать railway.json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health"
  }
}

# Deploy
railway up

# Environment variables в Railway:
DATABASE_URL=<railway-provided-postgres-url>
SECRET_KEY=<generated-secret>
GOOGLE_CREDENTIALS_PATH=./service-account.json
GOOGLE_DRIVE_FOLDER_ID=<your-folder-id>
CORS_ORIGINS=https://your-frontend-domain.vercel.app
```

**Загрузить service-account.json через Railway CLI или dashboard.**

#### База данных

Использовать managed PostgreSQL от Railway, Supabase или AWS RDS.

---

### Вариант 2: Docker Compose (Single Server)

#### 1. Dockerfile для Backend

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. Dockerfile для Frontend

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### 3. nginx.conf для Frontend

```nginx
# frontend/nginx.conf
server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

#### 4. docker-compose.yml

```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: gallery
      POSTGRES_USER: gallery_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U gallery_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://gallery_user:${DB_PASSWORD}@db:5432/gallery
      SECRET_KEY: ${SECRET_KEY}
      GOOGLE_CREDENTIALS_PATH: /app/service-account.json
      GOOGLE_DRIVE_FOLDER_ID: ${GOOGLE_DRIVE_FOLDER_ID}
      CORS_ORIGINS: http://localhost:80
    volumes:
      - ./backend/service-account.json:/app/service-account.json:ro
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "8000:8000"

  frontend:
    build: ./frontend
    environment:
      VITE_API_URL: http://localhost:8000
    depends_on:
      - backend
    ports:
      - "80:80"

volumes:
  postgres_data:
```

#### 5. .env для Docker Compose

```bash
# .env
DB_PASSWORD=your_secure_password
SECRET_KEY=your_jwt_secret_key
GOOGLE_DRIVE_FOLDER_ID=your_folder_id
```

#### 6. Запуск

```bash
# Build и запуск
docker-compose up -d

# Применить миграции
docker-compose exec backend alembic upgrade head

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down

# Остановка с удалением volumes
docker-compose down -v
```

---

### Вариант 3: Kubernetes (Production Scale)

#### 1. Secrets

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: gallery-secrets
type: Opaque
stringData:
  DATABASE_URL: postgresql://user:pass@postgres:5432/gallery
  SECRET_KEY: your-jwt-secret-key
  GOOGLE_CREDENTIALS: |
    {
      "type": "service_account",
      "project_id": "your-project",
      ...
    }
  GOOGLE_DRIVE_FOLDER_ID: your-folder-id
```

#### 2. PostgreSQL Deployment

```yaml
# k8s/postgres.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        env:
        - name: POSTGRES_DB
          value: gallery
        - name: POSTGRES_USER
          value: gallery_user
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: gallery-secrets
              key: DB_PASSWORD
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
```

#### 3. Backend Deployment

```yaml
# k8s/backend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: your-registry/gallery-backend:latest
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: gallery-secrets
              key: DATABASE_URL
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: gallery-secrets
              key: SECRET_KEY
        - name: GOOGLE_DRIVE_FOLDER_ID
          valueFrom:
            secretKeyRef:
              name: gallery-secrets
              key: GOOGLE_DRIVE_FOLDER_ID
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: backend
spec:
  selector:
    app: backend
  ports:
  - port: 8000
    targetPort: 8000
```

#### 4. Frontend Deployment

```yaml
# k8s/frontend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: your-registry/gallery-frontend:latest
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: frontend
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 80
```

#### 5. Ingress

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: gallery-ingress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - gallery.example.com
    secretName: gallery-tls
  rules:
  - host: gallery.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: backend
            port:
              number: 8000
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 80
```

#### 6. Deploy

```bash
# Apply all configs
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/backend.yaml
kubectl apply -f k8s/frontend.yaml
kubectl apply -f k8s/ingress.yaml

# Check status
kubectl get pods
kubectl get services
kubectl get ingress

# Run migrations
kubectl exec -it <backend-pod-name> -- alembic upgrade head

# View logs
kubectl logs -f deployment/backend
```

---

## CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Test Backend
        run: |
          cd backend
          pip install -r requirements.txt
          pytest

      - name: Test Frontend
        run: |
          cd frontend
          npm ci
          npm run build

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build and push Docker images
        run: |
          docker build -t registry.example.com/gallery-backend:latest ./backend
          docker build -t registry.example.com/gallery-frontend:latest ./frontend
          docker push registry.example.com/gallery-backend:latest
          docker push registry.example.com/gallery-frontend:latest

      - name: Deploy to Kubernetes
        run: |
          kubectl rollout restart deployment/backend
          kubectl rollout restart deployment/frontend
```

---

## Мониторинг и логирование

### 1. Health Check Endpoint

Уже реализован в `main.py`:

```python
@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

### 2. Логирование

```python
# backend/main.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"{request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Status: {response.status_code}")
    return response
```

### 3. Prometheus Metrics

```bash
pip install prometheus-fastapi-instrumentator
```

```python
# backend/main.py
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

Instrumentator().instrument(app).expose(app)
# Metrics доступны на /metrics
```

### 4. Grafana Dashboard

Импортировать dashboard для FastAPI и PostgreSQL.

---

## Безопасность в Production

### 1. HTTPS

Использовать Let's Encrypt с Certbot:

```bash
sudo certbot --nginx -d gallery.example.com
```

### 2. Environment Variables

**НЕ хранить credentials в коде!**

Использовать:
- `.env` файлы (не в Git)
- Secrets в Kubernetes
- Environment variables в облачных платформах

### 3. Rate Limiting

```bash
pip install slowapi
```

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/auth/login")
@limiter.limit("5/minute")
async def login(...):
    ...
```

### 4. CORS

Настроить только необходимые origins:

```python
CORS_ORIGINS = "https://gallery.example.com"
```

### 5. Database Security

- Использовать SSL для PostgreSQL
- Регулярные backups
- Ограничить доступ по IP

---

## Масштабирование

### Horizontal Scaling

**Backend:**
- Несколько инстансов за Load Balancer
- Stateless архитектура (JWT)
- Shared PostgreSQL

**Frontend:**
- CDN для статики (CloudFlare)
- Multiple replicas

**Database:**
- Read replicas для SELECT запросов
- Connection pooling (PgBouncer)

### Caching

```bash
pip install redis
```

```python
import redis

cache = redis.Redis(host='localhost', port=6379, db=0)

@app.get("/photos/{photo_id}")
def get_photo(photo_id: int):
    # Check cache
    cached = cache.get(f"photo:{photo_id}")
    if cached:
        return StreamingResponse(io.BytesIO(cached))
    
    # Fetch from Drive
    file_content = drive_service.get_file(...)
    
    # Cache for 1 hour
    cache.setex(f"photo:{photo_id}", 3600, file_content)
    
    return StreamingResponse(io.BytesIO(file_content))
```

---

## Стоимость развертывания

### Бесплатный вариант (MVP):

- Frontend: Vercel Free Tier
- Backend: Railway Free Tier (500 часов/месяц)
- Database: Railway Free Tier (до 500MB)
- Storage: Google Drive Free (15GB)

**Итого: $0/месяц**

### Платный вариант (Production):

- Frontend: Vercel Pro ($20/месяц)
- Backend: Railway Pro ($5-20/месяц)
- Database: Railway Postgres ($10/месяц)
- Storage: Google Drive Business (100GB, $2/месяц)
- Domain: $10-15/год

**Итого: ~$40-55/месяц**

---

## Troubleshooting

### Backend не запускается

```bash
# Проверить логи
docker-compose logs backend

# Проверить переменные окружения
docker-compose exec backend env

# Проверить подключение к БД
docker-compose exec backend python -c "from app.core.database import engine; print(engine.url)"
```

### Frontend не подключается к Backend

- Проверить CORS settings в backend
- Проверить `VITE_API_URL` в frontend
- Проверить proxy в `vite.config.ts`

### Google Drive errors

- Проверить `service-account.json`
- Проверить, что папка расшарена на Service Account
- Проверить `GOOGLE_DRIVE_FOLDER_ID`

---

## Заключение

Выбор варианта развертывания зависит от ваших требований:

- **Локальная разработка:** Simple local setup
- **MVP/Demo:** Vercel + Railway (бесплатно)
- **Small production:** Docker Compose на VPS
- **Enterprise:** Kubernetes с автомасштабированием

Архитектура Gallery позволяет легко мигрировать между вариантами по мере роста нагрузки.
