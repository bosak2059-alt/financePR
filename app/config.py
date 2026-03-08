import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

class Config:
    """Класс конфигурации приложения Flask"""
    
    # Секретный ключ
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    
    # Получаем переменные с значениями по умолчанию
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_HOST = os.environ.get('MYSQL_HOST', '127.0.0.1')
    MYSQL_PORT = os.environ.get('MYSQL_PORT', '3306')  # Теперь по умолчанию 3306
    MYSQL_DB = os.environ.get('MYSQL_DB', 'finance_tracker')
    
    # Формируем строку подключения
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:"
        f"{MYSQL_PASSWORD}@"
        f"{MYSQL_HOST}:"
        f"{MYSQL_PORT}/"
        f"{MYSQL_DB}"
    )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False