# Инструкция по развертыванию на Heroku

## Быстрый старт

### 1. Установите Heroku CLI
Скачайте с https://devcenter.heroku.com/articles/heroku-cli

### 2. Войдите в Heroku
```bash
heroku login
```

### 3. Создайте приложение
```bash
heroku create more-lazarevskoe
```

### 4. Добавьте файлы в Git
```bash
git add .
git commit -m "Initial commit"
```

### 5. Разверните на Heroku
```bash
git push heroku main
```

### 6. Откройте сайт
```bash
heroku open
```

## Альтернативные платформы

### Railway
1. Зайдите на https://railway.app
2. Подключите GitHub репозиторий
3. Выберите папку с проектом
4. Railway автоматически развернет приложение

### Render
1. Зайдите на https://render.com
2. Создайте новый Web Service
3. Подключите GitHub репозиторий
4. Выберите Python и укажите команду: `python app.py`

### PythonAnywhere
1. Зайдите на https://pythonanywhere.com
2. Создайте бесплатный аккаунт
3. Загрузите файлы через веб-интерфейс
4. Настройте WSGI файл

## Настройка для продакшена

### Переменные окружения
Добавьте в настройки Heroku:
```
SECRET_KEY=your-secret-key-here
FLASK_ENV=production
```

### База данных
Для продакшена рекомендуется использовать PostgreSQL:
```bash
heroku addons:create heroku-postgresql:hobby-dev
```

## Обновление сайта
После изменений в коде:
```bash
git add .
git commit -m "Update"
git push heroku main
```
