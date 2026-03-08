import pymysql
from dotenv import load_dotenv
import os

# Загружаем .env из папки base
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'base', '.env'))

try:
    connection = pymysql.connect(
        host=os.environ.get('MYSQL_HOST', '127.0.0.1'),
        port=int(os.environ.get('MYSQL_PORT', 3306)),
        user=os.environ.get('MYSQL_USER', 'root'),
        password=os.environ.get('MYSQL_PASSWORD', '1403'),
        database=os.environ.get('MYSQL_DB', 'finance_tracker')
    )
    print("✅ УСПЕХ! Подключение к MySQL работает.")
    connection.close()
except pymysql.err.OperationalError as e:
    print(f"❌ ОШИБКА: {e}")
    print("\nВозможные причины:")
    print("1. Неверный пароль в .env")
    print("2. Пользователь не имеет доступа с 'localhost'")
    print("3. База данных не существует")