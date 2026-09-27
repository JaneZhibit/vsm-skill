# ВСМ-Тренажер (VSM Conductor Simulator)

**🌐 Live сайт:** [https://vsm-skill.ru](https://vsm-skill.ru)

Интерактивный тренажер проводников высокоскоростного поезда (ВСМ-1 Москва — Санкт-Петербург). Архитектура проекта построена по принципу монорепозитория с разделением на бэкенд-сервисы, современный реактивный интерфейс и инфраструктурные конфигурации развертывания.

> ⚠️ **ВАЖНО:** Для работы симулятора и генерации ИИ-пассажиров требуется наличие ключа от API Polza.ai. Обязательно укажите `POLZA_AI_API_KEY` в вашем файле `.env` перед запуском!

---

## Архитектура монорепозитория

```
HSM_msk_transport/
├── .agents/                    # Агентские навыки и стандарты разработки
│   └── skills/stack.md         # Описание стека и обязательных правил
├── backend/                    # Сервисы бэкенда (Python 3.12, FastAPI)
│   ├── app/
│   │   ├── api/                # Версионированные API маршруты
│   │   │   └── v1/
│   │   │       ├── endpoints/  # Конечные точки API (health, scenarios, etc.)
│   │   │       └── api.py      # Агрегатор роутов v1
│   │   ├── core/               # Ядро приложения и конфигурация
│   │   │   └── config.py       # pydantic-settings, автопоиск .env, PROJECT_ROOT
│   │   ├── schemas/            # Pydantic v2 схемы валидации
│   │   │   └── health.py       # Схемы мониторинга состояния
│   │   ├── services/           # Бизнес-логика тренажера и сценариев
│   │   └── main.py             # Точка входа FastAPI, CORS, lifespan
│   ├── Dockerfile              # Контейнеризация бэкенда (python:3.12-slim)
│   └── requirements.txt        # Зависимости Python
├── frontend/                   # Клиентская часть (Bun + Svelte 5 + TailwindCSS)
│   ├── src/
│   │   ├── App.svelte          # Главный экран (Svelte 5 Runes, индикатор связи)
│   │   ├── app.css             # Стили TailwindCSS v4
│   │   └── main.ts             # Точка монтирования SPA
│   ├── vite.config.ts          # Конфигурация Vite + dev-прокси на /api
│   ├── svelte.config.js        # Конфигурация компилятора Svelte
│   ├── Dockerfile              # Мультистейдж сборка (oven/bun + nginx)
│   └── package.json            # Зависимости и скрипты фронтенда
├── deploy/                     # Конфигурации развертывания и инфраструктуры
│   ├── docker-compose.yml      # Локальный и staging запуск сервисов
│   └── nginx.conf              # Reverse proxy для маршрутизации /api/ и статики
├── .env.example                # Шаблон переменных окружения
├── .env                        # Локальная конфигурация (игнорируется в git)
├── .gitignore                  # Настройки исключений репозитория
└── README.md                   # Документация проекта
```

---

## Требования к окружению

- **Python**: 3.11+ (рекомендуется 3.12)
- **Bun**: 1.1+ (строго используется Bun вместо npm/yarn для работы с фронтендом)
- **Docker & Docker Compose**: для контейнеризированного запуска

---

## Быстрый локальный запуск

### 1. Переменные окружения
При первом клонировании убедитесь, что в корне проекта существует файл `.env` (он уже предсоздан на основе `.env.example`):
```bash
cp .env.example .env
```
Откройте файл `.env` и **обязательно** заполните ключ от Polza API:
```env
POLZA_AI_API_KEY=ваш_секретный_ключ
```

### 2. Запуск Backend (FastAPI)
Из корневой папки проекта:
```powershell
# Установка зависимостей (если еще не установлены)
.\.venv\Scripts\pip.exe install -r backend\requirements.txt

# Запуск dev-сервера с hot-reload
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000
```
- Документация Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Эндпоинт Health Check: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

### 3. Запуск Frontend (Svelte 5 + Bun)
В отдельном окне терминала:
```powershell
cd frontend
bun install
bun dev
```
- Приложение будет доступно по адресу: [http://localhost:5173](http://localhost:5173)
- Запросы к `/api/*` автоматически проксируются Vite dev-сервером на `http://127.0.0.1:8000`.

---

## Запуск в Docker Compose

Для одновременного запуска всех сервисов (бэкенд, фронтенд, reverse proxy Nginx):

```powershell
docker compose -f deploy/docker-compose.yml up --build
```

- Веб-приложение (через Nginx Gateway): [http://localhost](http://localhost)
- Backend API напрямую: [http://localhost:8000/docs](http://localhost:8000/docs)
- Frontend Dev-сервер напрямую: [http://localhost:5173](http://localhost:5173)

---

## Стандарты разработки

1. **Python / Backend**:
   - Весь код пишется строго асинхронным (`async/await`) с явными аннотациями типов (`Type Hints`).
   - Валидация строго через **Pydantic v2**.
   - Все пути вычисляются от `PROJECT_ROOT` или `BACKEND_DIR` через `pathlib.Path`.
2. **Frontend**:
   - Команды фронтенда запускаются строго через `bun`.
   - Актуальный синтаксис **Svelte 5** (Runes: `$state`, `$derived`, `$props`).
   - Стилизация компонентов через **TailwindCSS**.
