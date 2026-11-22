# OrderFlow — backend

REST API сервиса заказов на разработку сайтов, Telegram-ботов и автоматизацию.
Клиент создаёт заказ, следит за его статусом и может отменить его, пока заказ новый.
Менеджер видит заказы всех клиентов и меняет их статусы по допустимым переходам.

## Стек

- Python 3.14, FastAPI, Pydantic 2
- SQLAlchemy 2, PostgreSQL 18, Alembic
- JWT (PyJWT, HS256), Argon2 (pwdlib) для хеширования паролей
- Docker Compose

## Быстрый старт (Docker)

1. Создайте файл с переменными окружения из шаблона:

   ```bash
   cp app/.env.example app/.env
   ```

2. Заполните `app/.env` (см. таблицу ниже). `POSTGRES_PASSWORD` должен совпадать с `DB_PASSWORD`, а `POSTGRES_USER` — с `DB_USER`.

3. Запустите:

   ```bash
   docker compose up --build
   ```

При старте контейнер API по очереди:
1. ждёт, пока PostgreSQL пройдёт healthcheck;
2. применяет миграции (`alembic upgrade head`);
3. создаёт аккаунт менеджера из `MANAGER_EMAIL` и `MANAGER_PASSWORD`, если его ещё нет;
4. запускает uvicorn.

После запуска:
- API: http://localhost:8080/api/v1
- Swagger UI: http://localhost:8080/docs
- Проверка работы: http://localhost:8080/api/v1/health → `{"status": "ok"}`

Остановить: `docker compose down`. Остановить и удалить данные БД: `docker compose down -v`.

> PostgreSQL читает `POSTGRES_USER` и `POSTGRES_PASSWORD` только при первом создании базы.
> Если вы поменяли их после первого запуска, удалите том командой `docker compose down -v`.

## Переменные окружения (`app/.env`)

| Переменная | Назначение |
|---|---|
| `DB_USER` | Пользователь БД, под которым подключается API |
| `DB_PASSWORD` | Пароль этого пользователя |
| `POSTGRES_USER` | Пользователь, которого создаёт контейнер PostgreSQL (то же значение, что `DB_USER`) |
| `POSTGRES_PASSWORD` | Его пароль (то же значение, что `DB_PASSWORD`) |
| `SECRET_KEY` | Ключ подписи JWT — длинная случайная строка, например `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `MANAGER_EMAIL` | Email аккаунта менеджера, который создаёт seed-скрипт |
| `MANAGER_PASSWORD` | Пароль менеджера, не короче 8 символов: короче не пропустит валидация входа |

Файл `app/.env` не попадает ни в Git (`.gitignore`), ни в Docker-образ (`.dockerignore`). В репозитории лежит только шаблон `app/.env.example`.

## API

Базовый префикс: `/api/v1`. Защищённые методы требуют заголовок `Authorization: Bearer <token>`.

| Метод | Путь | Кто может | Назначение |
|---|---|---|---|
| GET | `/health` | все | Проверка работы API |
| POST | `/auth/register` | все | Регистрация клиента → 201 |
| POST | `/auth/login` | все | Получение JWT → 200 |
| GET | `/auth/me` | авторизованный | Данные текущего пользователя |
| POST | `/orders` | клиент | Создание заказа → 201 |
| GET | `/orders` | клиент / менеджер | Клиент видит свои заказы, менеджер — все; сортировка от новых к старым |
| GET | `/orders/{id}` | клиент / менеджер | Один заказ; чужой заказ для клиента — 404 |
| PATCH | `/orders/{id}/status` | менеджер | Смена статуса по допустимым переходам |
| POST | `/orders/{id}/cancel` | клиент | Отмена своего заказа в статусе `new` |

Примеры запросов:

```bash
# регистрация
curl -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name": "Alex", "email": "alex@example.com", "password": "StrongPass123!"}'

# вход
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "alex@example.com", "password": "StrongPass123!"}'

# создание заказа
curl -X POST http://localhost:8080/api/v1/orders \
  -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  -d '{"title": "Telegram-бот для магазина", "description": "Нужен бот для обработки заказов покупателей.", "budget_rub": 15000}'
```

Полное описание схем запросов и ответов — в Swagger UI (`/docs`).

### Роли

- **client** — создаётся публичной регистрацией. Роль нельзя передать в запросе.
- **manager** — создаётся только seed-скриптом `app/scripts/seed_manager.py`.

### Статусы заказа

Новый заказ получает статус `new`. Менеджеру доступны переходы:

```
new         → in_progress | canceled
in_progress → ready       | canceled
ready       → completed
```

`completed` и `canceled` — конечные статусы. Клиент может только отменить собственный заказ, пока тот в статусе `new`.
Таблица переходов: `app/core/order_status.py`.

### Коды ошибок

| Код | Когда |
|---|---|
| 401 | Нет токена, токен недействителен или просрочен, неверный email или пароль |
| 403 | Недостаточно прав для действия |
| 404 | Заказ не существует или принадлежит другому клиенту |
| 409 | Email уже зарегистрирован или переход статуса запрещён |
| 422 | Данные запроса не прошли валидацию |

Ограничения полей: имя — 2–50 символов, пароль — 8–128, название заказа — 5–120, описание — 20–2000, бюджет — целое число от 1000 до 500000.

## Миграции

Миграции лежат в `migrations/versions`. В Docker они применяются автоматически при старте. Вручную внутри контейнера:

```bash
docker compose exec order_flow_backend alembic upgrade head
```

Новая миграция после изменения моделей:

```bash
docker compose exec order_flow_backend alembic revision --autogenerate -m "описание"
```

Сгенерированный файл нужно проверить глазами и закоммитить.

## Структура проекта

```
app/
  api/
    routes/          HTTP-маршруты: health, auth, orders
    dependencies.py  внедрение сессии БД и сервисов
  core/              настройки, хеширование паролей, таблица переходов статусов
  db/                engine и сессии SQLAlchemy
  jwt_token/         создание и проверка JWT
  models/            ORM-модели (users, orders)
  repositories/      запросы к БД
  schemas/           Pydantic-схемы запросов и ответов
  services/          бизнес-логика и границы транзакций
  scripts/           seed-скрипт менеджера
migrations/          Alembic
Dockerfile
docker-compose.yaml
```

Запрос проходит по цепочке: route → service (проверка прав, бизнес-правила, `commit`) → repository (SQL) → PostgreSQL.

## Frontend

Веб-интерфейс на Next.js живёт в отдельном проекте и обращается к этому API по адресу из `NEXT_PUBLIC_API_URL=http://localhost:8080/api/v1`.
CORS разрешён для `http://localhost:3000` и `http://172.19.0.1:3000` (`app/core/settings.py`).

## Ограничения текущей версии

- Хост БД в `app/core/settings.py` зашит как `postgres`, поэтому приложение запускается только через Docker Compose. Для запуска без Docker нужно брать хост и порт из переменных окружения.
- Автотестов пока нет.
- Нет refresh-токенов: JWT живёт 30 минут, после этого нужно войти заново.
