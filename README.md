# Hearthstone Deck Helper

Вспомогательный сервис для игроков [Hearthstone](https://playhearthstone.com/) и организаторов фан-турниров.  

> Доступен на http://91.227.18.9/

> Это новая, полностью переписанная версия [старого проекта](https://github.com/ysaron/NeuraHS). Использованы более новые версии Python и Django. Проект докеризован, отрефакторен и избавлен от бесполезных фич.

## Описание

**Hearthstone** - коллекционная карточная игра, в которой колоды составляются из 30 карт и копируются из клиента игры как байтовые строки в Base64 (чтобы ими было удобно делиться).  
Основная функция сервиса - расшифровка таких строк (кодов колоды) по известному алгоритму и удобный просмотр колод.  

### Стэк
- Python 3.10
- Django 4
- Django REST Framework
- PostgreSQL 14
- Docker & docker-compose
- Nginx
- Gunicorn
- HTML & CSS & JavaScript

### Функционал

- **Расшифровка кодов колод и их детализированный просмотр**  
  "Сырой" вид прямо из клиента игры также поддерживается.
- **База данных колод**  
  Расшифрованные колоды сохраняются и доступны для просмотра, в т.ч., посредством API.
- **Личное хранилище колод пользователя**[^1]  
  Требует авторизации.
- **Подробная информация о составе колоды**  
  Полезно для организаторов турниров с особыми требованиями к составлению колод.
- **Рендеринг подробного изображения колоды в высоком разрешении**  
  Полезно при заявлении колод на турниры.
- **База данных карт Hearthstone**  
  В т.ч. неколлекционные карты, недоступные для включения в колоду.  
  БД собирается из открытых API:  
  - https://rapidapi.com/omgvamp/api/hearthstone - данные
  - https://hearthstonejson.com - изображения
- **Открытый API для read-only доступа к картам и колодам**
  - поиск карт и колод по названию, классам, типам, форматам
  - поиск колод по включенным картам
  - расшифровка кода колоды
  - документация, сгенерированная Swagger
- **Статистика по картам и колодам**

### Реализовано
- **i18n & l10n (английский и русский язык)**  
  Переключение языка - на боковой панели.
- **Система аккаунтов**  
  - Регистрация с подтверждением email
  - Сброс пароля через email
- **Логирование ошибок в Django Middleware**
- **Юнит-тестирование (pytest)**
- **Контейнеризация (Docker, docker-compose)**
- **Деплой (Nginx + Gunicorn)**
  
## Локальная установка и запуск

> (!) Для работы сервису требуется предварительное заполнение БД и скачивание около 1.5 Гб изображений коллекционных карт, которое может занять несколько часов.  
> Изображения скачиваются по просьбе разработчиков [hearthstoneJSON.com](https://hearthstonejson.com/docs/images.html) для уменьшения нагрузки.  
> Проще просто посмотреть проект в уже развернутом виде: http://91.227.18.9/.

### Требования
- Docker
- docker-compose
- Git

### Установка

Клонировать репозиторий:
```shell
git clone https://github.com/ysaron/hearthstone-deck-helper.git
```

В корневом каталоге проекта создать `.env.dev` и задать в нем следующие переменные окружения:
```dotenv
DEBUG=1
SECRET_KEY="<your_secret_key>"
DJANGO_ALLOWED_HOSTS=".localhost 127.0.0.1 [::1]"
SQL_ENGINE=django.db.backends.postgresql
SQL_DATABASE=<your_local_db_name>
SQL_USER=<your_sql_user>
SQL_PASSWORD=<your_sql_password>
SQL_HOST=db
SQL_PORT=5432
DATABASE=postgres
X_RAPIDARI_KEY=<your_rapidapi_key>
```

`X_RAPIDARI_KEY` - токен для доступа к API с данными Hearthstone, получить нужно [здесь](https://rapidapi.com/omgvamp/api/hearthstone).

Для работы системы аккаунтов понадобится также электронная почта с настроенным SMTP и доп. переменные окружения:
```dotenv
EMAIL_HOST_USER
EMAIL_HOST_PASSWORD
```

### Запуск

Сборка образа + запуск:
```shell
docker-compose up -d --build
```

Переход в контейнер приложения: 
```shell
docker-compose exec web bash
```

Создание суперпользователя:
```shell
python manage.py createsuperuser
```

Сборка БД с картами + скачивание изображений коллекционных карт:
```shell
python manage.py update_db
```

Добавление в БД "starter pack" с колодами:
```shell
python manage.py import_decks
```

Выход из контейнера
```shell
exit
```

Сайт будет доступен на http://127.0.0.1:8000/.

Остановка:
```shell
docker-compose down
```

[^1]: Поскольку клиент игры на данный момент позволяет сохранять только 27 колод одновременно. Маловато? Маловато.
