# OrderFlow — backend

REST API сервиса заказов на разработку сайтов, Telegram-ботов и автоматизацию.
Клиент создаёт заказ, следит за его статусом и может отменить его, пока заказ новый.
Менеджер видит заказы всех клиентов и меняет их статусы по допустимым переходам.

## Стек

- Python 3.14, FastAPI, Pydantic 2
- SQLAlchemy 2, PostgreSQL 18, Alembic
- Redis 7 — кэш списков заказов
- JWT (PyJWT, HS256), Argon2 (pwdlib) для хеширования паролей
- Pytest
- Docker Compose

## Быстрый старт (Docker)

1. Создайте файл с переменными окружения из шаблона:

   ```bash
   cp app/.env.example app/.env
   ```

2. Заполните `app/.env` (см. таблицу ниже). `POSTGRES_PASSWORD` должен совпадать с `DB_PASSWORD`, а `POSTGRES_USER` — с `DB_USER`. Для Docker укажите `REDIS_URL=redis://redis:6379/0`.

3. Запустите:

   ```bash
   docker compose up --build
   ```

Compose поднимает три сервиса: `order_flow_backend` (API), `postgres` и `redis`. Наружу открыт только порт API.

При старте контейнер API по очереди:
1. ждёт, пока PostgreSQL и Redis пройдут healthcheck;
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
| `REDIS_URL` | Адрес Redis. В Docker — `redis://redis:6379/0`; если не задан, используется `redis://localhost:6379/0` |

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

Ошибки приходят в едином формате `{"detail": "..."}`. Сервисы выбрасывают собственные исключения (`UnauthorizedError`, `ForbiddenError`, `NotFoundError`, `ConflictError` в `app/exceptions/exceptions.py`), а обработчики из `app/exceptions/handlers.py` превращают их в HTTP-ответы. Любая ошибка JWT — просроченный, поддельный или битый токен — отдаётся как 401.

## Кэширование

Списки заказов (`GET /orders`) кэшируются в Redis по схеме cache-aside: сначала ответ ищется в кэше, при промахе берётся из PostgreSQL и кладётся в кэш.

| Ключ | Что хранит |
|---|---|
| `orders:user:{user_id}` | Список заказов конкретного клиента |
| `orders:all` | Список всех заказов для менеджера |

- Ключ выбирается по пользователю из токена, поэтому клиент никогда не получит чужой список.
- При создании, отмене и смене статуса заказа удаляются оба ключа — владельца заказа и `orders:all`. Удаление происходит после `commit`, чтобы в кэш не вернулись старые данные.
- Время жизни записи — 1 час (`cache_ttl_seconds` в `app/core/settings.py`).
- Если Redis недоступен, API продолжает работать напрямую с PostgreSQL: ошибки Redis только пишутся в лог (`app/cache/redis_cache.py`).

## Тесты

Тесты работают без PostgreSQL и Redis: база подменяется SQLite в памяти, кэш — заглушкой `FakeCache` (`tests/conftest.py`). Каждый тест начинается с пустой базы.

```bash
pip install -r requirements-dev.txt
pytest -v
```

Что покрыто:
- регистрация, вход и `/auth/me`, включая повторный email, неверный пароль и битый токен;
- доступ к заказам: клиент не видит чужой заказ, менеджер видит все;
- смена статуса: клиенту — 403, запрещённый переход — 409;
- отмена только нового заказа;
- обновление кэша: после смены статуса менеджером клиент сразу видит новый статус;
- таблица переходов статусов (unit-тест).

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
    dependencies.py  внедрение сессии БД, кэша и сервисов
  cache/             обёртка над Redis
  core/              настройки, хеширование паролей, таблица переходов статусов
  db/                engine и сессии SQLAlchemy
  exceptions/        исключения приложения и их обработчики
  jwt_token/         создание и проверка JWT
  models/            ORM-модели (users, orders)
  repositories/      запросы к БД
  schemas/           Pydantic-схемы запросов и ответов
  services/          бизнес-логика и границы транзакций
  scripts/           seed-скрипт менеджера
migrations/          Alembic
tests/               pytest: фикстуры в conftest.py, тесты auth и orders
Dockerfile
docker-compose.yaml
requirements.txt     зависимости приложения
requirements-dev.txt зависимости для разработки и тестов
```

Запрос проходит по цепочке: route → service (проверка прав, бизнес-правила, `commit`, инвалидация кэша) → repository (SQL) → PostgreSQL. Списки заказов сервис сначала ищет в Redis.

## Frontend

Веб-интерфейс на Next.js живёт в отдельном проекте и обращается к этому API по адресу из `NEXT_PUBLIC_API_URL=http://localhost:8080/api/v1`.
CORS разрешён для `http://localhost:3000` и `http://172.19.0.1:3000` (`app/core/settings.py`).

## Ограничения текущей версии

- Хост БД в `app/core/settings.py` зашит как `postgres`, поэтому приложение запускается только через Docker Compose. Для запуска без Docker нужно брать хост и порт из переменных окружения.
- Тесты используют SQLite, а не PostgreSQL: логику прав и статусов они проверяют, но поведение, специфичное для PostgreSQL (блокировки, часовые пояса), — нет.
- Кэшируются только списки заказов; отдельный заказ (`GET /orders/{id}`) всегда читается из БД.
- Нет refresh-токенов: JWT живёт 30 минут, после этого нужно войти заново.
