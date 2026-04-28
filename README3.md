# app.py
## 1 Импорты и зависимости
```
    from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
    from flask_login import LoginManager, login_user, logout_user, login_required, current_user
    from config import Config
    from models import db, User, Category, Transaction, Budget
    from forms import LoginForm, RegistrationForm, TransactionForm, BudgetForm
    from sqlalchemy import func, extract, and_
    from datetime import datetime, timedelta
    from decimal import Decimal
```

Для чего:
1. __flask__ – основной фреймворк для маршрутизации, рендеринга шаблонов, работы с HTTP-запросами и flash-сообщениями.

2. __flask_login__ – управление сессиями, защита маршрутов (@login_required), доступ к текущему пользователю (current_user).

3. __config__, __models__, __forms__ – внешние модули. config хранит настройки (URL БД, секретный ключ), models описывает таблицы SQLAlchemy, forms содержит классы WTForms для валидации ввода.

4. __sqlalchemy.func__, __extract__ – инструменты для агрегации (SUM, COUNT) и извлечения частей даты в SQL-запросах.

5. __datetime__, __timedelta__, __Decimal__ – работа с датами, расчёт периодов и точные финансовые вычисления (избегание ошибок плавающей запятой).

## 2 Создание приложения и инициализация (create_app)
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        db.create_all()
    ...

Для чего:
1. Factory-паттерн: Функция create_app() создаёт экземпляр Flask. Это стандарт для тестирования и разделения окружений (dev/prod).

2. app.config.from_object(Config) – подгружает настройки из класса Config.

3. db.init_app(app) – привязывает SQLAlchemy к приложению.

4. LoginManager – настраивает поведение аутентификации: куда редиректить неавторизованных (login_view), какое сообщение показывать.

5. @login_manager.user_loader – Flask-Login вызывает эту функцию для загрузки объекта User из БД по ID при каждом запросе.

6. with app.app_context(): db.create_all() – автоматически создаёт таблицы в БД при первом запуске.

## 3 Основные маршруты (Routes)
Главная страница / Дашборд (/)
@app.route('/')
@login_required
def index():

Для чего: **Отображает сводку финансов.**
1. Считает общий баланс: SUM(income) - SUM(expense) через JOIN Category.

2. Считает доходы/расходы за текущий месяц (фильтр по date >= first_day).

3. Забирает последние 10 транзакций для быстрого просмотра.

4. Формирует данные для графика категорий расходов (группировка по Category.name за месяц).

5. Формирует данные для графика трендов за 6 месяцев (цикл по месяцам, расчёт income/expense для каждого).

6. Всё передаётся в index.html (вероятно, для рендеринга через Jinja2 и отрисовки графиков через Chart.js).

**Аутентификация (/login, /register, /logout)**
1. /login: Проверяет логин/пароль через user.check_password(), создаёт сессию (login_user), редиректит на запрошенную страницу или дашборд.

2. /register: Создаёт нового пользователя, хеширует пароль (user.set_password), вызывает create_default_categories(), сохраняет в БД.

3. /logout: Очищает сессию (logout_user) и перенаправляет на вход.

**Управление транзакциями**
1. /add_transaction:
    (a)Определяет тип (income/expense) из формы или URL.
    (b)form.populate_categories(...) – динамически подгружает только нужные категории в форму.
    (c)При валидации создаёт объект Transaction, сохраняет, коммитит, показывает flash-сообщение.

2. /transaction/edit/<id> и /transaction/delete/<id>:
    (a)Проверяют права: if transaction.user_id != current_user.id: flash(...); return redirect(...) (защита от редактирования чужих записей).
    (b)Обновляют поля или удаляют запись через db.session.delete().
    (c)После операций перенаправляют на отчёты.

**Отчёты (/reports)**
1. Принимает параметры фильтрации: date_from, date_to, category.
2. Строит динамический query с последовательными .filter().
3. Использует query.paginate(page, per_page=20) для постраничной навигации.
4. Считает общую сумму по текущим фильтрам через отдельный запрос с func.sum().
5. Передаёт данные в reports.html для отображения таблицы и пагинации.

## 4 Вспомогательные функции
def create_default_categories(user_id):
    defaults = [('Зарплата', 'income'), ('Еда', 'expense'), ...]
    for name, type_ in defaults:
        category = Category(user_id=user_id, name=name, type=type_)
        db.session.add(category)
    db.session.commit()

Для чего: Автоматически создаёт базовый набор категорий при регистрации. Это улучшает UX: пользователю не нужно вручную добавлять "Еду", "Транспорт" и т.д. перед первой записью.

## 5 Ключевые архитектурные и технические особенности
| **Элемент** | **Что делает** | **Зачем нужен** |
| --- | --- | --- |
| `@login_required` | Блокирует доступ к маршрутам без авторизации | Безопасность данных |
| `JOIN Category` | Связывает транзакции с категориями для фильтрации по `type` | Позволяет разделять доходы/расходы на уровне БД |
| `func.sum(…).scalar() or 0` | Считает сумму, возвращает `0` вместо `None` | Избегает ошибок типа `TypeError` при арифметике |
| `query.paginate()` | Разбивает результат на страницы | Оптимизация загрузки при больших объёмах данных |
| `current_user.id` | ID вошедшего пользователя из сессии | Изоляция данных между пользователями (multi-tenancy) |

# config.py – Управление настройками приложения

__Назначение__
Централизованное хранение конфигурации Flask-приложения. Отделяет настройки от бизнес-логики, обеспечивает безопасную работу с секретами через переменные окружения и формирует строку подключения к базе данных.

import os
from dotenv import load_dotenv
    1. **os** – стандартный модуль для работы с путями файловой системы.
    2. **load_dotenv** – загружает переменные из файла .env в os.environ, чтобы приложение могло их читать.

BASE_DIR = os.path.abspath(os.path.dirname(file))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
ENV_PATH = os.path.join(PROJECT_ROOT, 'base', '.env')
load_dotenv(ENV_PATH)
    __Для чего:__ Вычисляет абсолютный путь до корня проекта, чтобы .env загружался независимо от того, из какой директории запускается скрипт.

class Config:
SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    __Для чего__: SECRET_KEY используется Flask для подписи cookies, сессий и защиты от CSRF. В продакшене обязательно должен быть случайной строкой, храниться только в .env.

MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
__остальные переменные с дефолтами__
SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
SQLALCHEMY_TRACK_MODIFICATIONS = False
    __Для чего__: Формирует URI для SQLAlchemy. Префикс mysql+pymysql указывает на использование драйвера PyMySQL.
    __SQLALCHEMY_TRACK_MODIFICATIONS = False__ отключает отслеживание изменений объектов ORM, что экономит оперативную память и повышает производительность.

UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'uploads')
__Для чего__: Резервирует папку для будущих функций загрузки файлов (аватары, чеки, экспорт отчётов).

# forms.py – Валидация и обработка пользовательского ввода
__Назначение__
Описывает структуры веб-форм с помощью Flask-WTF/WTForms. Обеспечивает автоматическую CSRF-защиту, валидацию данных на сервере, безопасное преобразование типов и динамическое наполнение выпадающих списков.

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DecimalField, ...
from wtforms.validators import DataRequired, Email, EqualTo, ...
    __Для чего__: FlaskForm автоматически добавляет скрытое поле csrf_token в каждую форму. validators проверяют данные до попадания в бизнес-логику.

__LoginForm__ и __RegistrationForm__
1. DataRequired, Length, Email – базовые проверки формата и обязательности.
2. EqualTo('password') – гарантирует совпадение пароля и его подтверждения.
3. validate_username, validate_email – кастомные валидаторы. WTForms автоматически вызывает методы validate_<имя_поля>(), если они существуют. Они делают запрос к БД, чтобы не допустить дубликатов.

__TransactionForm__
class TransactionForm(FlaskForm):
    type = SelectField(...)
    category = SelectField(..., coerce=int)
    amount = DecimalField(..., places=2)
    date = DateField(..., format='%Y-%m-%d')
    description = TextAreaField(...)

__Для чего__: coerce=int автоматически преобразует выбранный id категории из строки в число. places=2 ограничивает деньги двумя знаками после запятой.
__populate_categories(self, user_id, trans_type)__ – ключевой метод. Вместо статического списка категорий он делает запрос Category.query.filter_by(...) и подставляет только нужные варианты (доходы/расходы) конкретного пользователя. Это предотвращает XSS и логические ошибки при выборе чужих категорий.

__BudgetForm__

1. Поля для установки лимитов: выбор категории, сумма (DecimalField), период (weekly/monthly).
2. Готовит базу для функции контроля расходов (в app.py пока не используется, но модель Budget уже готова).

# models.py – Схема базы данных (SQLAlchemy ORM)

__Назначение__
Определяет структуру реляционной базы данных, связи между таблицами, правила целостности данных и методы работы с ними на уровне объектов Python.


from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
db = SQLAlchemy()
1. SQLAlchemy() – экземпляр ORM. Инициализируется глобально, привязывается к приложению в create_app() через db.init_app(app).
2. UserMixin – добавляет методы is_authenticated, is_active, is_anonymous, get_id(), требуемые Flask-Login.

__User (Пользователь)__
tablename = 'users'  # ⚠️ Должно быть __tablename__ = 'users'
username = db.Column(db.String(80), unique=True, nullable=False, index=True)
password_hash = db.Column(db.String(255), nullable=False)

1. index=True – создаёт B-Tree индекс для ускорения поиска по логину/email.
2. transactions = db.relationship(..., cascade='all, delete-orphan') – важная настройка. При удалении пользователя автоматически удаляются все его транзакции, категории и бюджеты. Предотвращает ForeignKeyViolation.
3. set_password / check_password – используют werkzeug.security для хеширования (PBKDF2). Пароли никогда не хранятся в открытом виде.

__Category (Категория)__
type = db.Column(db.String(10), nullable=False)  # 'income' или 'expense'
icon = db.Column(db.String(50), default='bi-circle')
__table_args__ = (
    db.UniqueConstraint('user_id', 'name', 'type', name='unique_user_category'),
)

__Для чего__: UniqueConstraint гарантирует, что у одного пользователя не будет двух категорий с одинаковым именем и типом (например, две "Еды" типа expense).
__icon__ – резерв под Bootstrap Icons для фронтенда.

__Transaction (Транзакция)__
amount = db.Column(db.Numeric(10, 2), nullable=False)
__Для чего__: Numeric (или DECIMAL в SQL) используется вместо Float для денег. Float хранит числа в двоичном виде с плавающей точкой, что приводит к ошибкам округления (0.1 + 0.2 != 0.3). Numeric гарантирует точность до 2 знаков после запятой.
__@property def amount_float(self)__ – удобный геттер для шаблонов Jinja2, чтобы не писать float(transaction.amount) каждый раз.

__Budget (Бюджет/Лимит)__
1. Связывает пользователя, категорию и лимит суммы.
2. period – позволяет в будущем фильтровать лимиты по неделям/месяцам.
3. category = db.relationship('Category', backref='budgets') – двусторонняя связь: из категории можно получить все её бюджеты через cat.budgets.

# Как файлы связаны между собой?

| Файл | Роль в архитектуре | Связи |
|------|-------------------|-------|
| `config.py` | Инфраструктура | Поставляет `SECRET_KEY` и `SQLALCHEMY_DATABASE_URI` в `app.py` через `app.config.from_object(Config)`. |
| `models.py` | Данные | Экспортирует `db` и классы-сущности. `forms.py` импортирует `User`, `Category` для валидации. `app.py` использует их для запросов. |
| `forms.py` | Ввод/Валидация | Использует `models` для проверки уникальности и заполнения списков. Результат валидации передаётся в `app.py` для создания объектов. |
| `app.py` | Маршрутизация & Логика | Собирает всё вместе: берёт конфиг, инициализирует БД, обрабатывает формы, вызывает модели, рендерит шаблоны. |