# Импорт базового класса формы и полей из Flask-WTF/WTForms для валидации и рендеринга форм в HTML
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DecimalField, DateField, SelectField, TextAreaField
# Импорт встроенных валидаторов для проверки обязательности, формата, длины и совпадения полей
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange
# Импорт моделей БД для проверки уникальности данных при регистрации/создании транзакций
from models import User, Category
# Импорт объекта текущего авторизованного пользователя для фильтрации данных
from flask_login import current_user

class LoginForm(FlaskForm):
    """
    Форма входа в систему.
    Содержит поля для ввода логина и пароля. Валидаторы гарантируют, что поля не пустые и логин соответствует ограничениям длины.
    """
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class RegistrationForm(FlaskForm):
    """
    Форма регистрации нового пользователя.
    Включает проверку корректности email, минимальной длины пароля и обязательного совпадения пароля с подтверждением.
    """
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Подтверждение пароля', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')

    def validate_username(self, username):
        """
        Кастомный валидатор имени пользователя.
        Проверяет, существует ли уже пользователь с таким логином в БД. Если да — прерывает отправку формы с ошибкой.
        """
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Это имя пользователя уже занято')

    def validate_email(self, email):
        """
        Кастомный валидатор email.
        Проверяет уникальность почтового адреса в БД для предотвращения дублирования аккаунтов.
        """
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Этот email уже зарегистрирован')

class TransactionForm(FlaskForm):
    """
    Форма добавления/редактирования финансовой транзакции (доход или расход).
    Использует динамические списки категорий, которые подгружаются в зависимости от типа операции и пользователя.
    """
    type = SelectField('Тип операции', choices=[('expense', 'Расход'), ('income', 'Доход')], validators=[DataRequired()])
    category = SelectField('Категория', coerce=int, validators=[DataRequired()])
    amount = DecimalField('Сумма', validators=[DataRequired(), NumberRange(min=0.01)], places=2)
    date = DateField('Дата', validators=[DataRequired()], format='%Y-%m-%d')
    description = TextAreaField('Описание', validators=[Length(max=200)])
    submit = SubmitField('Сохранить')

    def __init__(self, *args, **kwargs):
        """
        Инициализатор формы. Вызывается при создании экземпляра.
        Подготавливает пустой список категорий, который позже заполняется методом populate_categories.
        """
        super(TransactionForm, self).__init__(*args, **kwargs)
        if 'user_id' in kwargs:
            kwargs.pop('user_id')
            self.category.choices = [(0, '-- Выберите категорию --')]

    def populate_categories(self, user_id, trans_type='expense'):
        """
        Метод для динамического заполнения выпадающего списка категорий.
        Запрашивает из БД только те категории, которые принадлежат текущему пользователю и соответствуют типу операции (доход/расход).
        """
        categories = Category.query.filter_by(user_id=user_id, type=trans_type).all()
        self.category.choices = [(0, '-- Выберите категорию --')] + [(c.id, c.name) for c in categories]

class BudgetForm(FlaskForm):
    """
    Форма установки лимита бюджета для конкретной категории.
    Позволяет задать сумму ограничения и период (неделя/месяц) для контроля расходов.
    """
    category = SelectField('Категория', coerce=int, validators=[DataRequired()])
    limit_amount = DecimalField('Лимит суммы', validators=[DataRequired(), NumberRange(min=0.01)], places=2)
    period = SelectField('Период', choices=[('weekly', 'Неделя'), ('monthly', 'Месяц')], validators=[DataRequired()])
    submit = SubmitField('Установить лимит')