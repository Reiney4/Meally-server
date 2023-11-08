from flask import Flask, request, jsonify, make_response, json
from flask_migrate import Migrate
from datetime import datetime, timedelta, timezone
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, JWTManager, get_jwt, get_jwt_identity, unset_jwt_cookies, jwt_required
from flask_cors import CORS
from models import db, User, Meal, Order, Caterer, Menu
from flask_login import current_user, LoginManager, login_required
from datetime import date
import sys
from os import path


sys.path.append(path.dirname(path.abspath(__file__)))
app = Flask(__name__)
jwt = JWTManager(app)
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = "login"
CORS(app, supports_credentials=True)


app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=5)
app.config["SECRET_KEY"] = 'OURSECRETKEYISSECRET'
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///mealy.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True


app.json.compact = False
app.json_as_ascii = False
db.init_app(app)

with app.app_context():
     db.create_all()


@app.route('/')
def index():
    return "Welcome to Mealy!"

# Register
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')

    if not (username and email and password):
        return jsonify({"message": "Missing required fields"}), 400

    user_exists = User.query.filter((User.username == username) | (User.email == email)).first()
    if user_exists:
        return jsonify({"message": "Username or email already exists"}), 409

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, email=email, password=hashed_password, role=role)
    db.session.add(new_user)
    db.session.commit()
    
    print(f"User registered: username={username}, email={email}, role={role}")

    if role in ['caterer', 'admin']:
        caterer = Caterer(user_id=new_user.id, name=username)
        db.session.add(caterer)
        db.session.commit()
        
        print(f"Caterer created: user_id={caterer.user_id}, name={caterer.name}")
        
    return jsonify({'message': 'Signed up successfully'}), 201

# Login route
@app.route('/login', methods=['POST'])
def login():
    auth = request.get_json()
    if not auth or not auth.get('username') or not auth.get('email') or not auth.get('password'):
        return make_response("Missing username and password", 401)

    user = User.query \
        .filter_by(username=auth.get('username'), email=auth.get('email')) \
        .first()
    if not user:
        return make_response("User does not exist.", 401)

    if bcrypt.check_password_hash(user.password, auth.get('password')):
        token = create_access_token({
            "id": user.id,
            "expires": datetime.utcnow() + timedelta(days=7),
            "role": user.role  # Include the user's role in the response
        }, app.config['SECRET_KEY'])
        return jsonify({
            "access-token": token,  # Change "access token" to "access_token"
            "message": "Logged in successfully",
            "role": user.role  # Include the user's role in the response
        })

    return make_response(
        'Could not verify',
        403,
        {'WWW-Authenticate': 'Basic realm = "Wrong password"'}
    )


# User profile
@app.route('/profile', methods=['GET'])
@jwt_required()
def user_profile(username):
    print(username)
    if not username:
        return jsonify({'No username found!'}), 404
    
    user = User.query.filter_by(username=username).first()
    print('user found is:', user)

    if not user:
        return jsonify({'User not found!'}), 404

    response_body = {
        'username' : user.username,
        'email' : user.email,
        'role' : user.role,
        'id' : user.id
    }

    return jsonify(response_body)

# Caterer login
@app.route('/caterer', methods=['POST'])
def caterer_login():
    data = request.get_json()
    email = request.json['email']
    password = request.json['password']
    role = 'caterer'

    user = User.query.filter_by(email=email, role=role).first()

    if not user:
        return jsonify({"Message":"User does not exist!"}), 401
    
    if bcrypt.check_password_hash(user.password, password):
        token = create_access_token({'id':user.id, 'role': user.role})
        return jsonify({
            "access_token": token, 
            "message":"Logged in successfully!"
            })
    
    return jsonify({"message":"Invalid credentials!"}), 404

# Getting caterers
@app.route('/caterers', methods=['GET'])
def get_caterers():
    caterers = Caterer.query.all()
    caterer_data = [{"caterer_id": caterer.user_id, "name": caterer.name} for caterer in caterers]
    return jsonify({"caterers": caterer_data})
   

# Caterer's profile
@app.route('/caterer/info', methods=['GET'])
@jwt_required()
def get_caterer_info():
    current_user = get_jwt_identity()
    caterer = Caterer.query.filter_by(user_id=current_user['id']).first()

    if not caterer:
        return jsonify({'message': 'Caterer not found'}), 404

    response_body = {
        'name': caterer.name,
        'star_meal': caterer.star_meal,
        'created_at': caterer.created_at,
        'updated_at': caterer.updated_at
    }

    return jsonify(response_body)


# Refreshing JWT tokens
@app.after_request
def refresh_token(response):
    try:
        expiring_timestamp = get_jwt()['exp']
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
        if target_timestamp > expiring_timestamp:
            access_token = create_access_token(identity=get_jwt_identity())
            data = response.get_json()
            if type(data) is dict:
                data['access_token'] = access_token
                response.data = json.dumps(data)
        return response
    except (RuntimeError, KeyError):
        return response
    
# For protecting routes
@app.route('/protected_routes', methods=['GET'])
@jwt_required
def some_protected_route():
    print('Protected route!')
    current_user = get_jwt()
    
    if current_user["role"] != "user":
        return jsonify({"message": "Access denied"}), 403

    return jsonify({"message": "You have access as a user"})


# Password reset route
@app.route('/password', methods=['POST'])
@jwt_required()
def change_password():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()

    if not user:
        return jsonify({"message": "User not found"}), 404

    current_password = request.json['current_password']
    new_password = request.json['new_password']

    if not bcrypt.check_password_hash(user.password, current_password):
        return jsonify({"message": "Invalid password"}), 401

    hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
    user.password = hashed_password
    db.session.commit()

    return jsonify({"message": "Password changed successfully"}), 200


# Meals routes
@app.route('/meals', methods=['GET'])
def get_meals():
    meal_options = Meal.query.all()
    # print("meal_options:" meal_options)
    meal_options_list = [meal_option.to_dict() for meal_option in meal_options]
    return jsonify({"meal options": meal_options_list})
    

@app.route('/meals', methods=['POST'])
def add_meal():
    data = request.json

    meal_name = data.get('name')
    caterer_id = data.get('caterer_id')
    description = data.get('description')
    price = data.get('price')
    image_url = data.get('image_url')

    if not meal_name:
        return jsonify({"message": "Name is required"}), 400

    if caterer_id is None:
        return jsonify({"message": "Caterer ID is required"}), 400

    # Create a new meal with the specified attributes
    new_meal = Meal(name=meal_name, caterer_id=caterer_id, description=description, price=price, image_url=image_url)

    try:
        db.session.add(new_meal)
        db.session.commit()
        return jsonify({"message": "Meal added successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error adding meal: {str(e)}"}), 500

@app.route('/meals', methods=['PUT'])
def update_meal():
    meal_option_id = request.json.get('id')
    new_meal_option_name = request.json.get('name')
    
    meal_option = Meal.query.get(meal_option_id)
    if meal_option:
        meal_option.name = new_meal_option_name
        db.session.commit()
        return jsonify({"message": "Meal option updated successfully"})
    else:
        return jsonify({"message": "Meal option not found"})

@app.route('/meals', methods=['DELETE'])
def delete_meal():
    meal_option_id = request.json.get('id')
    
    meals = Meal.query.get(meal_option_id)
    if meals:
        db.session.delete(meals)
        db.session.commit()
        return jsonify({"message": "Meal option deleted successfully"})
    else:
        return jsonify({"message": "Meal option not found"})

@app.route('/menu/<date>', methods=['POST'])
def set_menu(date):
    menu_items = request.json.get('menu_items')
    menu = Menu(date=date, items=menu_items)
    db.session.add(menu)
    db.session.commit()
    return jsonify({"message": f"Menu set successfully for {date}"})

@app.route('/menu', methods=['GET'])
def get_menu():
    menus = Menu.query.all()
    menus_list = [menu.to_dict() for menu in menus]
    # print(menus_list)
    return jsonify({"menus": menus_list})

@app.route('/orders', methods=['POST'])
@jwt_required()
def add_order():
    try:
        current_user_id = get_jwt_identity()
       
        data = request.get_json()
        meal_id = data.get('meal_id')
        quantity = data.get('quantity')

        if meal_id is None or quantity is None:
            return jsonify({"error": "Missing data in the request"}), 400

        meal = Meal.query.get(meal_id)

        if meal is None:
            return jsonify({"error": "Meal not found"}), 404
        
        total_amount = meal.price * quantity

        orders = Order(
            user_id=current_user_id,
            meal_id=meal_id,
            quantity=quantity,
            total_amount=total_amount,
            created_at=datetime.utcnow()
        )

        db.session.add(orders)
        db.session.commit()

        return jsonify({"message": "Order added successfully"}), 201

    except Exception as e:
        return jsonify({"error": "Failed to add the order", "message": str(e)}), 500



@app.route('/orders', methods=['GET'])
def view_orders():
    orders = Order.query.all()
    orders_list = [order.to_dict() for order in orders]
    return jsonify({"orders": orders_list})

@app.route('/order/<order_id>', methods=['PUT'])
def change_order_status(order_id):
    new_status = request.json.get('new_status')
    order = Order.query.get(order_id)
    if order:
        order.status = new_status
        db.session.commit()
        return jsonify({"message": "Order status changed successfully"})
    else:
        return jsonify({"message": "Order not found"})

# @app.route('/earnings', methods=['GET'])
# def view_earnings():
#     earnings = calculate_earnings()
#     return jsonify({"earnings": earnings})

# def calculate_earnings():
#     orders = Order.query.all()
#     earnings = 0
#     for order in orders:
#         earnings += order.price

#     return earnings


@login_manager.user_loader
def load_user(user_id):
    # Implement a function that retrieves a user by their ID from the database
    return User.query.get(int(user_id))

@app.route('/earnings', methods=['GET'])
@login_required
def view_caterer_earnings():
    if current_user.role != 'caterer' and current_user.role != 'admin':
        return jsonify({"error": "Only caterers or admins can view earnings"})


    today = date.today()
    earnings = calculate_caterer_earnings(current_user.id, today)
    return jsonify({"earnings": earnings})


def calculate_caterer_earnings(caterer_id, date):
    # Perform a database query to fetch orders for the given caterer and date, and sum their total amounts
    orders = Order.query.filter_by(user_id=caterer_id).filter_by(order_date=date).all()
    total_earnings = sum(order.total_amount for order in orders)

    return total_earnings


@app.route('/logout', methods=['POST'])
def logout():
    response = jsonify({'Message': "Successfully logged out"})
    unset_jwt_cookies(response)
    return response

if __name__ == "_main_":
    app.run(debug=True, port=5555)