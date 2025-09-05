# ArticleHub API

## Опис

**ArticleHub API** — це REST API-сервіс для управління користувачами та статтями, побудований на Django + DRF, з MongoDB, асинхронними задачами через Celery, запуском у Docker та деплоєм на AWS EC2.

---

## Функціонал

- **User Management:** Реєстрація, логін (JWT), профіль
- **Articles CRUD:** Створення, читання, оновлення, видалення статей
- **Пошук та фільтрація статей**
- **Swagger-документація**
- **Асинхронні задачі (Celery):**
  - Вітальний email після реєстрації (імітація)
  - Аналіз статті (підрахунок слів, унікальних тегів)
  - Періодична статистика по статтях (celery-beat)
- **Тести (pytest / Django tests)**
- **CI/CD (GitHub Actions)**
- **Деплой на AWS EC2 через Docker**
- **Nginx reverse proxy + HTTPS (Let's Encrypt)**
- **MongoDB Atlas підтримується**

---

## Швидкий старт

`https://lightray.live/docs/` - Swagger документація на продакшн
Можно ознайомитись і швидко протестувати API онлайн.

### 1. Клонування репозиторію

```bash
git clone https://github.com/kukalets-sergiy/ArticleHub-API.git
cd ArticleHub-API
```

### 2. Налаштування змінних середовища

- Створіть `.env` файл на основі прикладу:
  ```bash
  cp .env.example .env
  ```
- Для продакшну використовуйте `.env.prod.example` (налаштуйте реальні секрети!)

### 3. Запуск локально (Docker Compose)

```bash
docker-compose up --build
```
- API: http://localhost:8000/
- Swagger: http://localhost:8000/swagger/

### 4. Тестування

```bash
docker-compose run --rm test
```

---

## Деплой на AWS EC2

1. **Запустіть сервер EC2 (Ubuntu 22.04).**
2. **Встановіть Docker та docker-compose:**
   ```bash
   sudo apt update && sudo apt install -y docker.io docker-compose
   sudo usermod -aG docker $USER
   ```
3. **Склонуйте репозиторій і налаштуйте .env.prod**
4. **Запустіть продакшн за допомогою Docker Compose:**
   ```bash
   docker-compose -f docker-compose.prod.yml up --build -d
   ```
5. **Nginx reverse proxy та HTTPS:**
   - Nginx розгортається в контейнері.
   - Сертифікати отримуються автоматично через Let's Encrypt (certbot).
   - Всі налаштування у папці `nginx/` та у `docker-compose.prod.yml`.

---

## Основні ендпоінти

### Аутентифікація

- **POST** `/api/v1/auth/register/` — реєстрація користувача
- **POST** `/api/v1/auth/login/` — вхід, отримання JWT
- **GET** `/api/v1/auth/profile/` — поточний профіль (JWT required)

### Статті

- **POST** `/api/v1/articles/` — створити статтю
- **GET** `/api/v1/articles/` — список статей (пошук, фільтрація)
- **GET** `/api/v1/articles/{id}/` — переглянути статтю
- **PUT** `/api/v1/articles/{id}/` — оновити статтю (автор)
- **DELETE** `/api/v1/articles/{id}/` — видалити статтю (автор)
- **POST** `/api/v1/articles/{id}/analyze/` — асинхронний аналіз статті (Celery)

---

## Swagger / Документація

- Swagger доступний за шляхом `https://lightray.live/docs/`, `http://localhost:8000/docs/` після запуску API.

---

## CI/CD

- Налаштовано через GitHub Actions для автоматичних тестів та деплою.

---

## Асинхронні задачі

- **Вітальний email** — Celery-таск після реєстрації (імітація логом)
   результат можна подивитись в консолі виконавши команду:
   ```bash
  cat /tmp/welcome_emails.log
    ```
- **Аналіз статті** — Celery-таск, результат зберігається в полі `analysis` статті
- **Періодична статистика** — Celery-beat (раз на добу), логування кількості статей
які зберігаються в logs/article_stats.log

---

## Тести

- Pytest або Django tests.
- Запуск:
  ```bash
  docker-compose run --rm test
  ```

---

## Приклади .env

- Дивись `.env.example` та `.env.prod.example` у корені проекту

---


## Ліцензія

MIT License
