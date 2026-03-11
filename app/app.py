from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from models import db, User, Category, Transaction, Budget
from forms import LoginForm, RegistrationForm, TransactionForm, BudgetForm
from sqlalchemy import func, extract, and_
from datetime import datetime, timedelta
from decimal import Decimal

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Инициализация расширений
    db.init_app(app)
    
    # Настройка LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице'
    login_manager.login_message_category = 'warning'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Создание таблиц БД при первом запуске
    with app.app_context():
        db.create_all()
        # Создаем стандартные категории для новых пользователей (опционально)
        # create_default_categories()
    
    # ================= МАРШРУТЫ =================
    
    @app.route('/')
    @login_required
    def index():
        """Главная страница - Дашборд"""
        now = datetime.now()
        first_day = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Расчет баланса (все доходы - все расходы)
        total_income = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user.id,
            Transaction.category.has(type='income')
        ).scalar() or 0
        
        total_expense = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user.id,
            Transaction.category.has(type='expense')
        ).scalar() or 0
        
        balance = float(total_income) - float(total_expense)
        
        # Доходы и расходы за текущий месяц
        income_month = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user.id,
            Transaction.category.has(type='income'),
            Transaction.date >= first_day
        ).scalar() or 0
        
        expense_month = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user.id,
            Transaction.category.has(type='expense'),
            Transaction.date >= first_day
        ).scalar() or 0
        
        # Последние 10 транзакций
        transactions = Transaction.query.filter_by(user_id=current_user.id)\
            .order_by(Transaction.date.desc()).limit(10).all()
        
        # Данные для графика категорий (расходы за месяц)
        category_stats = db.session.query(
            Category.name, func.sum(Transaction.amount).label('total')
        ).join(Transaction).filter(
            Transaction.user_id == current_user.id,
            Transaction.category.has(type='expense'),
            Transaction.date >= first_day
        ).group_by(Category.name).all()
        
        # Данные для графика трендов (последние 6 месяцев)
        trend_stats = []
        for i in range(5, -1, -1):
            date = now - timedelta(days=i*30)
            month_start = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = (month_start + timedelta(days=32)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            inc = db.session.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == current_user.id,
                Transaction.category.has(type='income'),
                Transaction.date >= month_start,
                Transaction.date < month_end
            ).scalar() or 0
            
            exp = db.session.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == current_user.id,
                Transaction.category.has(type='expense'),
                Transaction.date >= month_start,
                Transaction.date < month_end
            ).scalar() or 0
            
            trend_stats.append({
                'month': month_start.strftime('%b'),
                'income': float(inc),
                'expense': float(exp)
            })
        
        return render_template('index.html',
                             balance=balance,
                             income_month=float(income_month),
                             expense_month=float(expense_month),
                             transactions=transactions,
                             category_stats=[{'name': s.name, 'total': float(s.total)} for s in category_stats],
                             trend_stats=trend_stats)
    
    @app.route('/templates/login', methods=['GET', 'POST'])
    def login():
        """Страница входа"""
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=True)
                next_page = request.args.get('next')
                flash('Вы успешно вошли!', 'success')
                return redirect(next_page if next_page else url_for('index'))
            else:
                flash('Неверное имя пользователя или пароль', 'danger')
        
        return render_template('/login.html', form=form)
    
    @app.route('/templates/register', methods=['GET', 'POST'])
    def register():
        """Страница регистрации"""
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        form = RegistrationForm()
        if form.validate_on_submit():
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            
            # Создаем стандартные категории для нового пользователя
            create_default_categories(user.id)
            
            flash('Регистрация успешна! Теперь вы можете войти', 'success')
            return redirect(url_for('login'))
        
        return render_template('register.html', form=form)
    
    @app.route('/templates/logout')
    @login_required
    def logout():
        """Выход из системы"""
        logout_user()
        flash('Вы вышли из системы', 'info')
        return redirect(url_for('login'))
    
    @app.route('/templates/add_transaction', methods=['GET', 'POST'])
    @login_required
    def add_transaction():
        """Добавление транзакции"""
        form = TransactionForm()
        form.populate_categories(current_user.id, 'expense')
        
        # Обновляем выбор категорий при смене типа операции (через JS лучше, но здесь для примера)
        if request.method == 'GET':
            trans_type = request.args.get('type', 'expense')
            form.populate_categories(current_user.id, trans_type)
        
        if form.validate_on_submit():
            transaction = Transaction(
                user_id=current_user.id,
                category_id=form.category.data,
                amount=form.amount.data,
                date=form.date.data,
                description=form.description.data
            )
            db.session.add(transaction)
            db.session.commit()
            flash('Транзакция успешно добавлена', 'success')
            return redirect(url_for('index'))
        
        return render_template('add_transaction.html', form=form)
    
    @app.route('/templates/reports')
    @login_required
    def reports():
        """Страница отчетов"""
        # Получаем параметры фильтра
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        category_id = request.args.get('category')
        page = request.args.get('page', 1, type=int)
        
        # Базовый запрос
        query = Transaction.query.filter_by(user_id=current_user.id)\
            .order_by(Transaction.date.desc())
        
        # Применяем фильтры
        if date_from:
            query = query.filter(Transaction.date >= datetime.strptime(date_from, '%Y-%m-%d'))
        if date_to:
            query = query.filter(Transaction.date <= datetime.strptime(date_to, '%Y-%m-%d'))
        if category_id and category_id != '':
            query = query.filter_by(category_id=int(category_id))
        
        # Пагинация
        pagination = query.paginate(page=page, per_page=20, error_out=False)
        transactions = pagination.items
        
        # Список категорий для фильтра
        categories = Category.query.filter_by(user_id=current_user.id).all()
        
        # Общая сумма по фильтру
        total = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user.id,
            *([Transaction.date >= datetime.strptime(date_from, '%Y-%m-%d')] if date_from else []),
            *([Transaction.date <= datetime.strptime(date_to, '%Y-%m-%d')] if date_to else []),
            *([Transaction.category_id == int(category_id)] if category_id and category_id != '' else [])
        ).scalar() or 0
        
        return render_template('reports.html',
                             transactions=transactions,
                             categories=categories,
                             date_from=date_from or '',
                             date_to=date_to or '',
                             total=float(total),
                             pagination=pagination,
                             current_page=page,
                             pages=pagination.pages)
    
    @app.route('/transaction/edit/<int:id>', methods=['GET', 'POST'])
    @login_required
    def edit_transaction(id):
        """Редактирование транзакции"""
        transaction = Transaction.query.get_or_404(id)
        if transaction.user_id != current_user.id:
            flash('Доступ запрещен', 'danger')
            return redirect(url_for('index'))
        
        form = TransactionForm(obj=transaction)
        form.populate_categories(current_user.id, transaction.category.type)
        
        if form.validate_on_submit():
            transaction.category_id = form.category.data
            transaction.amount = form.amount.data
            transaction.date = form.date.data
            transaction.description = form.description.data
            db.session.commit()
            flash('Транзакция обновлена', 'success')
            return redirect(url_for('reports'))
        
        return render_template('add_transaction.html', form=form, edit=True)
    
    @app.route('/transaction/delete/<int:id>')
    @login_required
    def delete_transaction(id):
        """Удаление транзакции"""
        transaction = Transaction.query.get_or_404(id)
        if transaction.user_id != current_user.id:
            flash('Доступ запрещен', 'danger')
            return redirect(url_for('index'))
        
        db.session.delete(transaction)
        db.session.commit()
        flash('Транзакция удалена', 'success')
        return redirect(url_for('reports'))
    
    # ================= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =================
    
    def create_default_categories(user_id):
        """Создает стандартные категории для нового пользователя"""
        defaults = [
            ('Зарплата', 'income'),
            ('Подработка', 'income'),
            ('Еда', 'expense'),
            ('Транспорт', 'expense'),
            ('Жилье', 'expense'),
            ('Развлечения', 'expense'),
            ('Здоровье', 'expense'),
            ('Одежда', 'expense'),
        ]
        for name, type_ in defaults:
            category = Category(user_id=user_id, name=name, type=type_)
            db.session.add(category)
        db.session.commit()
    
        return app

    @app.route('/api/category_stats')
    def api_category_stats():
        """API: Статистика расходов по категориям за текущий месяц"""
        stats = db.session.query(
            Category.name,
            func.sum(Transaction.amount).label('total')
        ).join(Transaction).filter(
            Transaction.category_id == Category.id,
            Category.type == 'expense',
            extract('month', Transaction.date) == datetime.now().month,
            extract('year', Transaction.date) == datetime.now().year
        ).group_by(Category.name).all()
        
        return jsonify([
            {'name': name, 'total': float(total)} 
            for name, total in stats
        ])

    @app.route('/api/trend_stats')
    def api_trend_stats():
        """API: Динамика доходов/расходов за последние 6 месяцев"""
        # Получаем данные за последние 6 месяцев
        six_months_ago = datetime.now() - timedelta(days=180)
        
        trend = db.session.query(
            func.strftime('%Y-%m', Transaction.date).label('month'),
            Category.type,
            func.sum(Transaction.amount).label('total')
        ).join(Category).filter(
            Transaction.date >= six_months_ago
        ).group_by('month', Category.type).all()
        
        # Формируем структуру данных для графика
        result = {}
        for month, trans_type, total in trend:
            if month not in result:
                result[month] = {'month': month, 'income': 0, 'expense': 0}
            result[month][trans_type] = float(total)
        
        # Сортируем по месяцам и возвращаем список
        return jsonify(sorted(result.values(), key=lambda x: x['month']))
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)