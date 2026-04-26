# Импорт расширения SQLAlchemy для работы с реляционной БД через ORM
from flask_sqlalchemy import SQLAlchemy
# Импорт миксина UserMixin для интеграции моделей с Flask-Login (упрощает управление сессиями)
from flask_login import UserMixin
# Импорт функций для безопасного хеширования и проверки паролей
from werkzeug.security import generate_password_hash, check_password_hash
# Импорт datetime для автоматической установки даты создания записей
from datetime import datetime

# Инициализация экземпляра ORM. Будет привязан к приложению в create_app()
db = SQLAlchemy()

class User(UserMixin, db.Model):
    """
    Модель пользователя. Хранит учетные данные для входа и связывает все остальные данные (транзакции, категории, бюджеты) с конкретным аккаунтом.
    Наследует UserMixin для методов is_authenticated, is_active, is_anonymous, get_id.
    """
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True) # Индекс ускоряет поиск по логину
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False) # Хранится только хеш, а не сам пароль
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Отношения "один ко многим". cascade='all, delete-orphan' автоматически удаляет связанные данные при удалении пользователя
    transactions = db.relationship('Transaction', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    categories = db.relationship('Category', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    budgets = db.relationship('Budget', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        """Хеширует переданный пароль с помощью werkzeug и сохраняет в БД"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Сравнивает переданный пароль с сохраненным хешем. Возвращает True при совпадении"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        """Строковое представление объекта для отладки"""
        return f'<User {self.username}>'

class Category(db.Model):
    """
    Модель категории расходов/доходов. Привязана к пользователю, чтобы у каждого были свои наборы категорий.
    """
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'income' или 'expense'
    icon = db.Column(db.String(50), default='bi-circle')  # Название иконки Bootstrap для фронтенда

    transactions = db.relationship('Transaction', backref='category', lazy='dynamic')

    # Уникальное ограничение: один пользователь не может иметь две категории с одинаковым именем и типом
    __table_args__ = (
        db.UniqueConstraint('user_id', 'name', 'type', name='unique_user_category'),
    )

    def __repr__(self):
        return f'<Category {self.name}>'

class Transaction(db.Model):
    """
    Модель финансовой транзакции. Фиксирует сумму, дату, описание и привязку к категории/пользователю.
    """
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False, index=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False) # Точное числовое представление денег
    date = db.Column(db.DateTime, default=datetime.utcnow, index=True) # Индекс для быстрых выборок по периодам
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Transaction {self.amount} {self.category.name}>'

    @property
    def amount_float(self):
        """Свойство для удобного преобразования Decimal в float при работе с фронтендом или графиками"""
        return float(self.amount)

class Budget(db.Model):
    """
    Модель бюджета (лимитов). Позволяет задать максимально допустимую сумму расходов по категории за определенный период.
    """
    __tablename__ = 'budgets'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    limit_amount = db.Column(db.Numeric(10, 2), nullable=False)
    period = db.Column(db.String(20), default='monthly')  # 'monthly' или 'weekly'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    category = db.relationship('Category', backref='budgets')

    def __repr__(self):
        return f'<Budget {self.limit_amount} for {self.category.name}>'