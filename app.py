from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///more_lazarevskoe.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Создаем папку для загрузок если её нет
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Модели базы данных
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связь с объявлениями
    listings = db.relationship('Listing', backref='author', lazy=True)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Связь с объявлениями
    listings = db.relationship('Listing', backref='category', lazy=True)

class Listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(300))
    rooms = db.Column(db.Integer)
    area = db.Column(db.Float)
    max_guests = db.Column(db.Integer)
    amenities = db.Column(db.Text)  # JSON строка с удобствами
    images = db.Column(db.Text)  # JSON строка с путями к изображениям
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Внешние ключи
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Маршруты
@app.route('/')
def index():
    # Получаем последние объявления
    listings = Listing.query.filter_by(is_active=True).order_by(Listing.created_at.desc()).limit(12).all()
    categories = Category.query.all()
    return render_template('index.html', listings=listings, categories=categories)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    category_id = request.args.get('category', '')
    min_price = request.args.get('min_price', '')
    max_price = request.args.get('max_price', '')
    location = request.args.get('location', '')
    
    # Базовый запрос
    listings_query = Listing.query.filter_by(is_active=True)
    
    # Применяем фильтры
    if query:
        listings_query = listings_query.filter(
            db.or_(
                Listing.title.contains(query),
                Listing.description.contains(query),
                Listing.location.contains(query)
            )
        )
    
    if category_id:
        listings_query = listings_query.filter_by(category_id=category_id)
    
    if min_price:
        listings_query = listings_query.filter(Listing.price >= int(min_price))
    
    if max_price:
        listings_query = listings_query.filter(Listing.price <= int(max_price))
    
    if location:
        listings_query = listings_query.filter(Listing.location.contains(location))
    
    listings = listings_query.order_by(Listing.created_at.desc()).all()
    categories = Category.query.all()
    
    return render_template('search.html', listings=listings, categories=categories, 
                         query=query, category_id=category_id, min_price=min_price, 
                         max_price=max_price, location=location)

@app.route('/listing/<int:listing_id>')
def listing_detail(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    return render_template('listing_detail.html', listing=listing)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        phone = request.form.get('phone', '')
        
        # Проверяем, что пользователь не существует
        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Пользователь с таким email уже существует')
            return render_template('register.html')
        
        # Создаем нового пользователя
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            phone=phone
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('Регистрация успешна! Теперь вы можете войти в систему.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/create_listing', methods=['GET', 'POST'])
@login_required
def create_listing():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        price = int(request.form['price'])
        location = request.form['location']
        address = request.form.get('address', '')
        rooms = int(request.form.get('rooms', 0)) if request.form.get('rooms') else None
        area = float(request.form.get('area', 0)) if request.form.get('area') else None
        max_guests = int(request.form.get('max_guests', 0)) if request.form.get('max_guests') else None
        category_id = int(request.form['category'])
        
        # Обработка удобств
        amenities = []
        for key in request.form:
            if key.startswith('amenity_'):
                amenities.append(key.replace('amenity_', ''))
        
        # Обработка загруженных изображений
        images = []
        if 'images' in request.files:
            files = request.files.getlist('images')
            for file in files:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    # Добавляем уникальный префикс
                    unique_filename = str(uuid.uuid4()) + '_' + filename
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    file.save(file_path)
                    images.append(unique_filename)
        
        # Создаем объявление
        listing = Listing(
            title=title,
            description=description,
            price=price,
            location=location,
            address=address,
            rooms=rooms,
            area=area,
            max_guests=max_guests,
            amenities=','.join(amenities),
            images=','.join(images),
            user_id=current_user.id,
            category_id=category_id
        )
        
        db.session.add(listing)
        db.session.commit()
        
        flash('Объявление успешно создано!')
        return redirect(url_for('listing_detail', listing_id=listing.id))
    
    categories = Category.query.all()
    return render_template('create_listing.html', categories=categories)

@app.route('/my_listings')
@login_required
def my_listings():
    listings = Listing.query.filter_by(user_id=current_user.id).order_by(Listing.created_at.desc()).all()
    return render_template('my_listings.html', listings=listings)

# Инициализация базы данных
def init_db():
    with app.app_context():
        db.create_all()
        
        # Создаем категории если их нет
        if not Category.query.first():
            categories = [
                Category(name='Койка-место', description='Размещение на койке в общем номере'),
                Category(name='Комната', description='Отдельная комната в квартире или доме'),
                Category(name='Квартира', description='Полная квартира для аренды'),
                Category(name='Дом', description='Частный дом или коттедж'),
                Category(name='Отель', description='Гостиничные номера'),
                Category(name='Хостел', description='Бюджетное размещение'),
                Category(name='Гостевой дом', description='Семейный гостевой дом'),
                Category(name='База отдыха', description='Размещение на базе отдыха')
            ]
            
            for category in categories:
                db.session.add(category)
            
            db.session.commit()
            print("База данных инициализирована!")

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
