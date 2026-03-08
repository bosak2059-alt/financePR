import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

class Config:
    """Класс конфигурации приложения Flask"""
    
    # Секретный ключ для сессий и CSRF-защиты
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    
    # Конфигурация базы данных MySQL
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.environ.get('MYSQL_USER')}:"
        f"{os.environ.get('MYSQL_PASSWORD')}@"
        f"{os.environ.get('MYSQL_HOST')}:"
        f"{os.environ.get('MYSQL_PORT')}/"
        f"{os.environ.get('MYSQL_DB')}"
    )
    
    # Отключаем отслеживание изменений объектов (экономит ресурсы)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Настройки сессий
    SESSION_COOKIE_SECURE = False  # True для HTTPS
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = 3600  # 1 час