# 🎮 GameStore — Django Backend

веб-застосунок магазину ігор на **Python 3.11 + Django 4.2 + PostgreSQL**.

---

## 📁 Структура проекту

```
gamestore/
├── gamestore/                  # Конфігурація Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── store/                      # Основний застосунок
│   ├── models.py               # Моделі БД
│   ├── serializers.py          # DRF серіалізатори
│   ├── views.py                # API ендпоінти
│   ├── urls.py                 # Маршрути
│   ├── admin.py                # Адмін-панель
│   ├── tests.py                # Тести
│   └── management/
│       └── commands/
│           └── seed.py         # Початкові дані
├── .github/
│   └── workflows/
│       └── ci-cd.yml           # GitHub Actions
├── Dockerfile
├── docker-compose.yml          # Локальна розробка
├── docker-compose.prod.yml     # Production
├── requirements.txt
├── manage.py
└── .env.example
```

---

## 🗄️ Моделі бази даних

| Модель | Опис |
|--------|------|
| `User` | Кастомний користувач (email як логін) |
| `Genre` | Жанри ігор |
| `Game` | Гра (ціна, знижка, системні вимоги) |
| `GameScreenshot` | Скріншоти гри |
| `Review` | Відгуки та рейтинги |
| `Cart` / `CartItem` | Кошик покупок |
| `Wishlist` | Список бажань |
| `Order` | Замовлення |
| `Library` / `LibraryGame` | Бібліотека ігор користувача |

---

## 🔌 API Ендпоінти

### Автентифікація
```
POST   /api/auth/register/     Реєстрація
POST   /api/auth/login/        Вхід (повертає JWT)
POST   /api/auth/logout/       Вихід (blacklist токена)
POST   /api/auth/refresh/      Оновити access-токен
GET    /api/auth/profile/      Профіль поточного юзера
PATCH  /api/auth/profile/      Оновити профіль
```

### Ігри
```
GET    /api/genres/                     Список жанрів
GET    /api/games/                      Список ігор (фільтри, пошук)
GET    /api/games/?search=cyber         Пошук
GET    /api/games/?genre=rpg            Фільтр по жанру
GET    /api/games/?on_sale=true         Тільки зі знижкою
GET    /api/games/?ordering=-price      Сортування
GET    /api/games/<slug>/               Деталі гри
POST   /api/games/<slug>/reviews/       Залишити відгук
```

### Кошик
```
GET    /api/cart/              Переглянути кошик
POST   /api/cart/              Додати гру { game_id: int }
DELETE /api/cart/              Видалити гру { game_id: int }
POST   /api/cart/checkout/     Оформити замовлення
```

### Список бажань
```
GET    /api/wishlist/          Переглянути wishlist
POST   /api/wishlist/          Додати гру { game_id: int }
DELETE /api/wishlist/          Видалити гру { game_id: int }
```

### Бібліотека
```
GET    /api/library/                    Ігри користувача
PATCH  /api/library/<game_id>/          Оновити (is_installed, play_time_minutes)
```

### Замовлення
```
GET    /api/orders/            Історія замовлень
```

---

## 🚀 Швидкий старт (Docker)

### 1. Клонуйте репозиторій
```bash
git clone https://github.com/Folldix/gamestore-django.git
cd gamestore-django
```

### 2. Налаштуйте змінні середовища
```bash
cp .env.example .env
# Відредагуйте .env під свої потреби
```

### 3. Запустіть через Docker Compose
```bash
docker compose up --build
```

Застосунок буде доступний на: http://localhost:8000  
Адмін-панель: http://localhost:8000/admin  
Логін адміна: `admin@gamestore.ua` / `Admin1234!`

---

## 🛠️ Локальна розробка (без Docker)

```bash
# Створити virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Встановити залежності
pip install -r requirements.txt

# Налаштувати .env (або експортувати змінні)
export DEBUG=True
export DB_HOST=localhost
export SECRET_KEY=dev-secret

# Міграції та seed
python manage.py migrate
python manage.py seed

# Запуск
python manage.py runserver
```

---

## 🧪 Тести

```bash
# Запуск тестів
python manage.py test store --verbosity=2

# З Docker
docker compose exec web python manage.py test store
```

---

## 🔐 GitHub Actions — необхідні Secrets

У налаштуваннях репозиторію (`Settings → Secrets → Actions`) додайте:

| Secret | Опис |
|--------|------|
| `DOCKERHUB_USERNAME` | Ваш логін на Docker Hub |
| `DOCKERHUB_TOKEN` | Access Token з Docker Hub |
| `SSH_HOST` | IP-адреса вашого сервера |
| `SSH_USER` | SSH-користувач (наприклад, `ubuntu`) |
| `SSH_PRIVATE_KEY` | Приватний SSH-ключ |
| `SSH_PORT` | SSH-порт (за замовчуванням `22`) |

---

## 🐳 CI/CD Pipeline

```
push → main
    │
    ├─ 1. 🧪 Test  (pytest + PostgreSQL service)
    │
    ├─ 2. 🐳 Build & Push Docker image → Docker Hub
    │         tags: latest + git SHA
    │
    └─ 3. 🚀 Deploy via SSH
              docker compose pull → up -d → migrate
```

### Підготовка сервера

```bash
# На вашому сервері
mkdir -p /opt/gamestore
cd /opt/gamestore

# Скопіюйте docker-compose.prod.yml та .env
scp docker-compose.prod.yml user@server:/opt/gamestore/
scp .env user@server:/opt/gamestore/

# Перший запуск
docker compose -f docker-compose.prod.yml up -d
```
# check