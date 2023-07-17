![Foodgram-project-react](https://https://github.com/Bogdanoo/foodgram-project-react/actions/workflows/main.yml/badge.svg)

# **Foodgram-project-react**

### Продуктовый помощник

# Описание

**«Продуктовый помощник»** - это сайт, на котором пользователи могут _публиковать_ рецепты, добавлять чужие рецепты в _избранное_ и _подписываться_ на публикации других авторов. Продуктовый помощник позволяет пользователям создавать список продуктов, которые нужно купить для приготовления выбранных блюд.


# Технологии

- Python 3.9
- Django 4.2.1
- Django Rest Framework 3.14.0
- PostgreSQL 13.0
- gunicorn 20.0.4
- nginx 1.21.3

# Контейнер

- Docker 24.0.2
- Docker Compose 2.18.1

# URL

- http://130.193.39.32

# Админ-панель

Данные для доступа в админ-панель:

email: bogdanzhovnir@gmail.com

password: 147369


# Локальная установка

Клонируйте репозиторий и перейдите в него в командной строке:
```sh
git clone https://github.com/Bogdanoo/foodgram-project-react.git && cd foodgram-project-react
```
Перейдите в директорию с файлом _Dockerfile_ и запустите сборку образа:
```sh
cd backend && docker build -t <DOCKER_USERNAME>/foodgram:<tag> .
```
Перейдите в директорию с файлом _docker-compose.yaml_:
```sh
cd ../infra
```
Создайте .env файл:
```sh
#.env
DB_ENGINE=<django.db.backends.postgresql>
DB_NAME=<имя базы данных postgres>
DB_USER=<пользователь бд>
DB_PASSWORD=<пароль>
DB_HOST=<db>
DB_PORT=<5432>
```
Запустите контейнеры:
```sh
docker compose up -d --build
```
После успешного запуска контейнеров выполните миграции в проекте:
```sh
docker compose exec backend python manage.py makemigrations
```
```sh
docker compose exec backend python manage.py migrate
```
Создайте суперпользователя:
```sh
docker compose exec backend python manage.py createsuperuser
```
Соберите статику:
```sh
docker compose exec backend python manage.py collectstatic --no-input
```
Наполните БД заготовленными ингредиентами:
```sh
docker compose exec backend python manage.py loaddatajson --filename ingredients.json
```

Создайте дамп (резервную копию) базы данных:
```sh
docker compose exec backend python manage.py dumpdata > fixtures.json
```
Для остановки контейнеров и удаления всех зависимостей воспользуйтесь командой:
```sh
docker compose down -v
```

# Примеры запросов

**GET**: http://127.0.0.1:8000/api/users/  
Пример ответа:
```json
{
  "count": 123,
  "next": "http://127.0.0.1:8000/api/users/?page=4",
  "previous": "http://127.0.0.1:8000/api/users/?page=2",
  "results": [
    {
      "email": "testuser@gmail.com",
      "id": 0,
      "username": "test.user",
      "first_name": "Test",
      "last_name": "User",
      "is_subscribed": false
    }
  ]
}
```

**POST**: http://127.0.0.1:8000/api/users/  
Тело запроса:
```json
{
  "email": "testuser@gmail.com",
  "username": "test.user",
  "first_name": "Test",
  "last_name": "User",
  "password": "Qwerty123"
}
```
Пример ответа:
```json
{
"email": "testuser@gmail.com",
"id": 0,
"username": "test.user",
"first_name": "Test",
"last_name": "User"
}
```

**GET**: http://127.0.0.1:8000/api/recipes/  
Пример ответа:
```json
{
  "count": 123,
  "next": "http://127.0.0.1:8000/api/recipes/?page=4",
  "previous": "http://127.0.0.1:8000/api/recipes/?page=2",
  "results": [
    {
      "id": 0,
      "tags": [
        {
          "id": 0,
          "name": "Завтрак",
          "color": "#E26C2D",
          "slug": "breakfast"
        }
      ],
      "author": {
        "email": "testuser@gmail.com",
        "id": 0,
        "username": "test.user",
        "first_name": "Test",
        "last_name": "User",
        "is_subscribed": false
      },
      "ingredients": [
        {
          "id": 0,
          "name": "Картофель отварной",
          "measurement_unit": "г",
          "amount": 1
        }
      ],
      "is_favorited": true,
      "is_in_shopping_cart": true,
      "name": "string",
      "image": "http://127.0.0.1:8000/media/recipes/images/image.jpeg",
      "text": "string",
      "cooking_time": 1
    }
  ]
}
```