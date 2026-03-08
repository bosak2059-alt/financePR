import os
from dotenv import load_dotenv

# Вычисляем путь к корневой папке проекта (на уровень выше от папки app)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)  # Поднимается из 'app' в 'finance'
ENV_PATH = os.path.join(PROJECT_ROOT, 'base', '.env')

# Загружаем переменные из конкретного пути
load_dotenv(ENV_PATH)

class Config:
    """Класс конфигурации приложения Flask"""
    
    # Секретный ключ
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    
    # Получаем переменные с значениями по умолчанию (защита от None)
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_HOST = os.environ.get('MYSQL_HOST', '127.0.0.1')
    MYSQL_PORT = os.environ.get('MYSQL_PORT', '3306')
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
    
    # Путь для загрузки файлов (если понадобится)
    UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'uploads')