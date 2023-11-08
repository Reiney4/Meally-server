from app import app
from faker import Faker
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
                # password="password",
            )
            caterers.append(caterer)

        db.session.add_all(caterers)
        db.session.commit()

    # Seed Meals
    def seed_meals():
        meals = [
            {
                "name": "Spaghetti Bolognese",
                "description": "A classic Italian dish featuring al dente spaghetti noodles topped with a rich and savory Bolognese sauce, made from ground beef, tomatoes, and aromatic herbs.",
                "price": 412.99,
                "image_url": "https://example.com/spaghetti_bolognese.jpg",
                "caterer_id": 1
            },
            {
                "name": "Grilled Salmon with Lemon-Dill Sauce",
                "description": "A healthy and flavorful option, this dish consists of grilled salmon fillets seasoned with herbs and served with a zesty lemon-dill sauce. Served alongside a medley of roasted vegetables, it's a perfect choice for those seeking a light and nutritious meal.",
                "price": 315.99,
                "image_url": "https://example.com/grilled_salmon.jpg",
                "caterer_id": 2
            },
            {
                "name": "Chicken Tikka Masala",
                "description": "A popular Indian dish, chicken tikka masala features tender pieces of marinated chicken in a creamy tomato-based sauce, spiced with aromatic Indian spices. It's typically served with fragrant basmati rice and naan bread.",
                "price": 614.99,
                "image_url": "https://example.com/chicken_tikka_masala.jpg",
                "caterer_id": 3
            },
            {
                "name": "Vegetable Stir-Fry",
                "description": "A vegetarian delight, this meal consists of a colorful mix of stir-fried vegetables like broccoli, bell peppers, carrots, and snap peas, cooked in a savory soy-based sauce. Served over steamed rice or noodles, it's a wholesome and quick option.",
                "price": 710.99,
                "image_url": "https://example.com/vegetable_stir_fry.jpg",
                "caterer_id": 4
            },
            {
                "name": "Margarita Pizza",
                "description": "A classic and simple Italian pizza, the Margarita pizza is topped with ripe tomatoes, fresh mozzarella cheese, basil leaves, and a drizzle of olive oil. The combination of these fresh ingredients creates a delightful and aromatic pizza.",
                "price": 911.99,
                "image_url": "https://example.com/margarita_pizza.jpg",
                "caterer_id": 5
            },
            {
                "name": "Beef Tacos",
                "description": "A Mexican favorite, beef tacos feature seasoned ground beef served in soft corn tortillas. Topped with shredded lettuce, diced tomatoes, cheese, and a dollop of sour cream, they are a satisfying and handheld delight.",
                "price": 299.99,
                "image_url": "https://example.com/beef_tacos.jpg",
                "caterer_id": 6
            },
            {
                "name": "Caesar Salad with Grilled Chicken",
                "description": "A Caesar salad consists of crisp romaine lettuce, croutons, and a creamy Caesar dressing. This version includes grilled chicken breast strips for added protein, making it a well-balanced and classic salad choice.",
                "price": 888.99,
                "image_url": "https://example.com/caesar_salad.jpg",
                "caterer_id": 7
            },
            {
                "name": "Shrimp Scampi Pasta",
                "description": "Shrimp scampi pasta combines succulent shrimp with linguine pasta in a garlic and white wine sauce. Garnished with fresh parsley and a sprinkle of Parmesan cheese, this dish is a seafood lover's dream.",
                "price": 616.99,
                "image_url": "https://example.com/shrimp_scampi_pasta.jpg",
                "caterer_id": 8
            },
            {
                "name": "Vegetable Curry",
                "description": "A vegetarian curry featuring a medley of colorful vegetables, simmered in a fragrant and spicy curry sauce. Served with steamed rice or naan bread, it's a flavorful and satisfying option for those who enjoy Indian cuisine.",
                "price": 712.99,
                "image_url": "https://example.com/vegetable_curry.jpg",
                "caterer_id": 9
            },
            {
                "name": "BBQ Pulled Pork Sandwich",
                "description": "A classic Southern barbecue specialty, this sandwich features tender, slow-cooked pulled pork smothered in smoky barbecue sauce. Served on a toasted bun with coleslaw, it's a hearty and finger-licking good meal.",
                "price": 611.99,
                "image_url": "https://example.com/bbq_pulled_pork_sandwich.jpg",
                "caterer_id": 10
            }
        ]

        for meal_data in meals:
            meal = Meal(
                caterer_id=meal_data["caterer_id"],
                name=meal_data["name"],
                description=meal_data["description"],
                price=meal_data["price"],
                image_url=meal_data["image_url"],
            )
            db.session.add(meal)

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
        menu_meals = set()  # Use a set to keep track of unique relationships
        while len(menu_meals) < num_menu_meals:
            menu_id = random.randint(1, db.session.query(Menu).count())
            meal_id = random.randint(1, db.session.query(Meal).count())
            # Check if the relationship already exists in the set
            if (menu_id, meal_id) not in menu_meals:
                menu_meals.add((menu_id, meal_id))
                menu_meal = MenuMeals(menu_id=menu_id, meal_id=meal_id)
                db.session.add(menu_meal)

        db.session.commit()

   # Seed Orders
def seed_orders(num_orders):
    orders = []
    for _ in range(num_orders):
        user_id = random.randint(1, db.session.query(User).count())
        meal_id = random.randint(1, db.session.query(Meal).count())
        meal = Meal.query.get(meal_id)
        quantity = random.randint(1, 5)
        total_amount = meal.price * quantity
        order = Order(
            user_id=user_id,
            meal_id=meal_id,
            quantity=quantity,
            total_amount=total_amount,
        )
        orders.append(order)

    db.session.add_all(orders)
    db.session.commit()

    # Seed data
with app.app_context():
    seed_users(10)  
    seed_caterers(5)  
    seed_meals()  
    seed_menus(5)  
    seed_menu_meals(20) 
    seed_orders(50) 
