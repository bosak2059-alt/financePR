from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

DB_URI = (
    f"mysql+pymysql://{os.environ.get('MYSQL_USER')}:"
    f"{os.environ.get('MYSQL_PASSWORD')}@"
    f"{os.environ.get('MYSQL_HOST')}:"
    f"{os.environ.get('MYSQL_PORT')}/"
    f"{os.environ.get('MYSQL_DB')}"
)

try:
    engine = create_engine(DB_URI)
    connection = engine.connect()
    print("✅ УСПЕХ! Python подключился к MySQL.")
    connection.close()
except Exception as e:
    print("❌ ОШИБКА подключения!")
    print(f"Детали: {e}")