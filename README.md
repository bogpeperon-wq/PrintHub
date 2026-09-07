# Print Hub

Telegram-сервис автоматической печати документов с интеграцией физического принтера Canon G3020.

## Архитектура

```
Telegram Bot → VPS (FastAPI, PostgreSQL, Redis) → Internet → MacBook (Print Agent) → CUPS → Canon G3020
```

## Компоненты

### VPS (Ubuntu + Docker)
- **PostgreSQL** — база данных
- **Redis** — очередь печати, кэш, блокировки
- **FastAPI** — REST API
- **Telegram Bot** — взаимодействие с пользователями
- **Worker** — фоновые задачи (обработка документов, уведомления)

### MacBook (Print Agent)
- **Print Agent** — приложение для управления печатью
- **CUPS** — система печати macOS
- **Canon G3020** — физический принтер

## Быстрый старт

### 1. Клонирование и настройка

```bash
cd /workspace
cp .env.example .env
# Отредактируйте .env с вашими данными
```

### 2. Запуск через Docker

```bash
docker-compose up -d
```

### 3. Миграции базы данных

```bash
docker-compose exec api alembic upgrade head
```

### 4. Проверка

```bash
# Telegram бот должен отвечать на /start
# Admin панель доступна через /admin (для администраторов)
```

## Конфигурация

### Переменные окружения

| Переменная | Описание | Пример |
|------------|----------|--------|
| `TELEGRAM_TOKEN` | Токен бота от @BotFather | `123:ABC...` |
| `ADMIN_IDS` | Telegram ID администраторов | `123456789,987654321` |
| `DATABASE_URL` | URL PostgreSQL | `postgresql+async://...` |
| `REDIS_URL` | URL Redis | `redis://localhost:6379/0` |
| `SECRET_KEY` | Секретный ключ | `random_string` |

### Print Agent на MacBook

1. Установите Python 3.12+
2. Настройте принтер в CUPS
3. Запустите агент:

```bash
cd print_agent
pip install -r requirements.txt
export SERVER_URL=https://your-vps.com
export AGENT_ID=agent_001
export AGENT_SECRET=secure_secret
python agent.py
```

## Поддерживаемые файлы

- PDF
- DOC, DOCX (требуется LibreOffice)
- JPG, JPEG, PNG

## Тарифы

- Ч/Б печать: 10 ₽/страница
- Цветная печать: 15 ₽/страница
- Фотографии: 25 ₽/страница
- Служебная страница: 5 ₽

## Безопасность

- Все секреты в environment variables
- HTTPS для всех внешних соединений
- Rate limiting для API
- Валидация MIME типов файлов
- SQL injection protection (SQLAlchemy)
- Idempotency для платежей и печати

## Мониторинг

- Health check endpoints
- Heartbeat от Print Agent
- Логирование всех операций
- Audit log действий администратора

## Разработка

### Запуск тестов

```bash
pytest tests/
```

### Type checking

```bash
mypy src/
```

### Linting

```bash
ruff check src/
```

## Документация

- [Deployment Guide](docs/deployment.md)
- [Print Agent Setup](docs/print_agent.md)
- [API Documentation](http://localhost:8000/docs)

## Лицензия

Proprietary — все права защищены.
