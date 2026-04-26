# Импорт модулей для работы с файловой системой и безопасной загрузки переменных окружения из .env файла
import os
from dotenv import load_dotenv

# Вычисление абсолютного пути к директории, где лежит данный файл (обычно 'app')
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
# Подъем на уровень выше для получения корневой папки проекта
PROJECT_ROOT = os.path.dirname(BASE_DIR)
# Формирование пути к файлу .env, который хранит секретные данные вне кода
ENV_PATH = os.path.join(PROJECT_ROOT, 'base', '.env')
# Загрузка переменных из .env в окружение процесса
load_dotenv(ENV_PATH)

class Config:
    """
    Класс конфигурации приложения Flask.
    Централизованно хранит все настройки: секретные ключи, параметры подключения к БД, пути к папкам.
    Используется для разделения логики и конфигурации, а также для безопасного управления чувствительными данными.
    """
    # Секретный ключ для подписи сессий, CSRF-токенов и куки. Берется из .env или используется заглушка для разработки
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'

    # Параметры подключения к MySQL. Значения по умолчанию защищают от ошибок, если переменные не заданы в .env
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_HOST = os.environ.get('MYSQL_HOST', '127.0.0.1')
    MYSQL_PORT = os.environ.get('MYSQL_PORT', '3306')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'finance_tracker')

    # Формирование строки подключения (Database URI) для SQLAlchemy в формате mysql+pymysql
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:"
        f"{MYSQL_PASSWORD}@"
        f"{MYSQL_HOST}:"
        f"{MYSQL_PORT}/"
        f"{MYSQL_DB}"
    )

    # Отключение отслеживания изменений моделей для экономии ресурсов и подавления предупреждений SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Абсолютный путь к папке для загрузки пользовательских файлов (на будущее)
    UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'uploads')