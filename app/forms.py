from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DecimalField, DateField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange
from models import User, Category
from flask_login import current_user


class LoginForm(FlaskForm):
    """Форма входа"""
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')


class RegistrationForm(FlaskForm):
    """Форма регистрации"""
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Подтверждение пароля', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Это имя пользователя уже занято')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Этот email уже зарегистрирован')


class TransactionForm(FlaskForm):
    """Форма добавления транзакции"""
    type = SelectField('Тип операции', choices=[('expense', 'Расход'), ('income', 'Доход')], validators=[DataRequired()])
    category = SelectField('Категория', coerce=int, validators=[DataRequired()])
    amount = DecimalField('Сумма', validators=[DataRequired(), NumberRange(min=0.01)], places=2)
    date = DateField('Дата', validators=[DataRequired()], format='%Y-%m-%d')
    description = TextAreaField('Описание', validators=[Length(max=200)])
    submit = SubmitField('Сохранить')
    
    def __init__(self, *args, **kwargs):
        super(TransactionForm, self).__init__(*args, **kwargs)
        # Динамическое заполнение категорий для текущего пользователя
        if 'user_id' in kwargs:
            user_id = kwargs.pop('user_id')
            # Фильтруем категории по типу и пользователю
            self.category.choices = [(0, '-- Выберите категорию --')]
    
    def populate_categories(self, user_id, trans_type='expense'):
        """Заполняет список категорий в зависимости от типа операции"""
        categories = Category.query.filter_by(user_id=user_id, type=trans_type).all()
        self.category.choices = [(0, '-- Выберите категорию --')] + [(c.id, c.name) for c in categories]


class BudgetForm(FlaskForm):
    """Форма установки бюджета"""
    category = SelectField('Категория', coerce=int, validators=[DataRequired()])
    limit_amount = DecimalField('Лимит суммы', validators=[DataRequired(), NumberRange(min=0.01)], places=2)
    period = SelectField('Период', choices=[('weekly', 'Неделя'), ('monthly', 'Месяц')], validators=[DataRequired()])
    submit = SubmitField('Установить лимит')