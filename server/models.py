import validators
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy.orm import validates
import bcrypt
from werkzeug.security import generate_password_hash


metadata = MetaData(naming_convention={
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
})

# Initialize a new SQLAlchemy instance. This is used in your Flask app to connect to the database.
db = SQLAlchemy(metadata=metadata)

# Custom exception for validation errors
class ValidationError(Exception):
    pass

# added serilization
class SerializerMixin:
    def as_dict(self):
        result = {}
        for c in self._table_.columns:
            result[c.name] = getattr(self, c.name)
        return result

# Define User model
class User(db.Model, SerializerMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    role = db.Column(db.String(20), nullable=False, default='customer')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)


    def __repr__(self):
        return f'<User(id={self.id}, username={self.username}, email={self.email}, role={self.role})>'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))



    @validates('email')
    def validate_email(self, key, address):
        if not validators.email(address):
            raise ValidationError(f'Invalid email address: {address}')
        return address

    @validates('username')
    def validate_username(self, key, username):
        if len(username) > 50:
            raise ValidationError('Username must be less than 50 characters')
        return username

# Define Caterer model
class Caterer(db.Model, SerializerMixin):
    __tablename__ = 'caterers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    # star_meal = db.Column(db.string(200), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Caterer(id={self.id}, name={self.name})>'


    @validates('name')
    def validate_name(self, key, name):
        if len(name) > 100:
            raise ValidationError('Name must be less than 100 characters')
        return name

# Define Meal model
class Meal(db.Model, SerializerMixin):
    __tablename__ = 'meals'
    id = db.Column(db.Integer, primary_key=True)
    caterer_id = db.Column(db.Integer, db.ForeignKey('caterers.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric, nullable=False)
    image_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Meal(id={self.id}, name={self.name}, price={self.price})>'


    @validates('image_url')
    def validate_image_url(self, key, url):
        if url and not validators.url(url):
            raise ValidationError(f'Invalid URL: {url}')
        return url

    @validates('name')
    def validate_name(self, key, name):
        if len(name) > 100:
            raise ValidationError('Name must be less than 100 characters')
        return name

    @validates('price')
    def validate_price(self, key, price):
        if price <= 0 or price > 10000:
            raise ValidationError('Price must be within the range of 0 to 10,000')
        return price

# Define Menu model
class Menu(db.Model, SerializerMixin):
    __tablename__ = 'menus'
    id = db.Column(db.Integer, primary_key=True)
    caterer_id = db.Column(db.Integer, db.ForeignKey('caterers.id'), nullable=False)
    day = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


    def __repr__(self):
        return f'<Menu(id={self.id}, day={self.day})>'


# Define MenuMeals model
class MenuMeals(db.Model, SerializerMixin):
    __tablename__ = 'menu_meals'
    menu_id = db.Column(db.Integer, db.ForeignKey('menus.id'), primary_key=True)
    meal_id = db.Column(db.Integer, db.ForeignKey('meals.id'), primary_key=True)

    def __repr__(self):
        return f'<MenuMeals(menu_id={self.menu_id}, meal_id={self.meal_id})>'

# Define Order model
class Order(db.Model, SerializerMixin):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    meal_id = db.Column(db.Integer, db.ForeignKey('meals.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_amount = db.Column(db.Numeric, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)


    def __repr__(self):
        return f'<Order(id={self.id}, user_id={self.user_id}, meal_id={self.meal_id}, quantity={self.quantity})>'

    @validates('quantity')
    def validate_quantity(self, key, quantity):
        if quantity <= 0:
            raise ValidationError('Quantity must be at least 1')
        return quantity

    @validates('total_amount')
    def validate_total_amount(self, key, amount):
        if amount <= 0:
            raise ValidationError('Total amount must be positive')
        return amount