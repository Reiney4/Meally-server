from app import app
from faker import Faker
from random import choice as rc
from models import db, User, Caterer, Meal, Menu, MenuMeals, Order
from datetime import datetime
import random

fake = Faker()

 # Clear existing data
with app.app_context():
   
    Caterer.query.delete()
    User.query.delete()
    Meal.query.delete()
    Menu.query.delete()
    MenuMeals.query.delete()
    Order.query.delete()



# Seed Users
def seed_users(num_users):
    users = []
    for _ in range(num_users):
        user = User(
            username=fake.user_name(),
            password="password",  # You should hash the passwords in a real scenario
            email=fake.email(),
            
        )
        users.append(user)

    db.session.add_all(users)
    db.session.commit()

# Seed Caterers
def seed_caterers(num_caterers):
    caterers = []
    for _ in range(num_caterers):
        caterer = Caterer(
            user_id=random.randint(1, db.session.query(User).count()),
            name=fake.company(),
        )
        caterers.append(caterer)

    db.session.add_all(caterers)
    db.session.commit()

# Seed Meals
def seed_meals(num_meals):
    meals = []
    for _ in range(num_meals):
        meal = Meal(
            caterer_id=random.randint(1, db.session.query(Caterer).count()),
            name=fake.bs(),
            description=fake.sentence(),
            price=random.uniform(5, 50),
        )
        meals.append(meal)

    db.session.add_all(meals)
    db.session.commit()

# Seed Menus
def seed_menus(num_menus):
    menus = []
    for _ in range(num_menus):
        menu = Menu(
            caterer_id=random.randint(1, db.session.query(Caterer).count()),
            day=fake.date_between(start_date='-1y', end_date='today'),
        )
        menus.append(menu)

    db.session.add_all(menus)
    db.session.commit()

# Seed MenuMeals
def seed_menu_meals(num_menu_meals):
    menu_meals = []
    for _ in range(num_menu_meals):
        menu_meal = MenuMeals(
            menu_id=random.randint(1, db.session.query(Menu).count()),
            meal_id=random.randint(1, db.session.query(Meal).count()),
        )
        menu_meals.append(menu_meal)

    db.session.add_all(menu_meals)
    db.session.commit()

# Seed Orders
def seed_orders(num_orders):
    orders = []
    for _ in range(num_orders):
        order = Order(
            user_id=random.randint(1, db.session.query(User).count()),
            meal_id=random.randint(1, db.session.query(Meal).count()),
            quantity=random.randint(1, 5),
            total_amount=0,  # You should calculate the total amount based on meal price and quantity
        )
        orders.append(order)

    db.session.add_all(orders)
    db.session.commit()

if __name__ == "__main__":
    num_users = 10
    num_caterers = 5
    num_meals = 20
    num_menus = 10
    num_menu_meals = 30
    num_orders = 50

    seed_users(num_users)
    seed_caterers(num_caterers)
    seed_meals(num_meals)
    seed_menus(num_menus)
    seed_menu_meals(num_menu_meals)
    seed_orders(num_orders)
