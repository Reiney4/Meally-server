from flask import Flask, request, jsonify, make_response, json
from flask_migrate import Migrate
from datetime import datetime, timedelta, timezone
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, JWTManager, get_jwt, get_jwt_identity, unset_jwt_cookies, jwt_required
from flask_cors import CORS
from models import db, User, Meal, Order, Caterer

app = Flask(__name__)
jwt = JWTManager(app)
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)
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

# user authentication.

# Sign up====working# Register
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
        caterer = Caterer(user_id=new_user.id, username=username, email=email)
        db.session.add(caterer)
        db.session.commit()
        
        print(f"Caterer created: user_id={caterer.user_id}, name={caterer.username}")
        
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
            "access_token": token,  # Change "access token" to "access_token"
            "message": "Logged in successfully",
            "role": user.role  # Include the user's role in the response
        })

    return make_response(
        'Could not verify',
        403,
        {'WWW-Authenticate': 'Basic realm = "Wrong password"'}
    )

    

# get all users
@app.route('/users', methods=['GET'])
@jwt_required()
def get_all_users():
    users = User.query.all()

    users_info = []

    for user in users:
        user_info = {
            'id': user.id,
            'username': user.username,  
            'email': user.email,          
            'password': user.password,
            'role': user.role,          
            'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': user.updated_at.strftime('%Y-%m-%d %H:%M:%S') if user.updated_at else None
        }
        users_info.append(user_info)

    return jsonify(users_info)

# to get a single user using the ID
@app.route('/user/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_by_id(user_id):

    username = get_jwt_identity()
    user = User.query.get(user_id)

    if user is None:
        return jsonify({'message': 'User not found'}), 404

    user_info = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'updated_at': user.updated_at.strftime('%Y-%m-%d %H:%M:%S') if user.updated_at else None
    }

    return jsonify(user_info)

# caterer can be able to manage orders

# @app.route('/profile', methods=['GET'])
# @jwt_required()
# def user_profile():

#     username = get_jwt_identity()
#     if not username:
#         return jsonify({'No username found!'}), 404
    
#     user = User.query.filter_by(username=username).first()
#     print('user found is:', user)

#     if not user:
#         return jsonify({'User not found!'}), 404

#     response_body = {
#         'username' : user.username,
#         'email' : user.email,
#         'role' : user.role,
#         'id' : user.id
#     }

#     return jsonify(response_body)

@app.route('/caterers', methods=['GET'])
def get_all_caterers():
    caterers = Caterer.query.all()
   
    caterers_info = []

    for caterer in caterers:
        caterer_info = {
            'id': caterer.id,
            'user_id': caterer.user_id,
            'username': caterer.username,
            'created_at': caterer.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': caterer.updated_at.strftime('%Y-%m-%d %H:%M:%S') if caterer.updated_at else None
        }
        caterers_info.append(caterer_info)

    return jsonify(caterers_info)



@app.route('/caterers', methods=['POST'])
def caterer_login():
    data = request.get_json()  # Parse JSON data from the request body

    email = data.get('email')  # Access 'email' from the parsed JSON data
    password = data.get('password')  # Access 'password' from the parsed JSON data
    role = 'caterer'

    user = User.query.filter_by(email=email, role=role).first()

    if not user:
        return jsonify({"Message": "User does not exist!"}), 401

    if bcrypt.check_password_hash(user.password, password):
        token = create_access_token({'id': user.id, 'role': user.role})
        return jsonify({"access_token": token, "message":"Logged in successfully"})

    return jsonify({"message": "Invalid credentials!"}), 404



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


@app.route('/meals', methods=['GET', 'POST', 'PUT', 'DELETE'])
@jwt_required()
def manage_meal_options():
    current_user = get_jwt()
    print(current_user)

    # Check if the user's role is 'admin' or 'caterer' to proceed
    if 'role' not in current_user or current_user['role'] not in ['caterer', 'admin']:
        return jsonify({"message": "Access denied"}), 403

    if request.method == 'GET':
        meal_options = Meal.query.all()
        meal_options_list = []

        for meal_option in meal_options:
            meal_option_dict = {
                'id': meal_option.id,
                'name': meal_option.name,
                'description': meal_option.description,
                'price': meal_option.price,
                'image_url': meal_option.image_url,
                'caterer_id': meal_option.caterer_id,
                # Add other meal attributes you want to include in the response
            }
            meal_options_list.append(meal_option_dict)

        return jsonify({"meal_options": meal_options_list})

    elif request.method == 'POST':
        meal_data = request.json
        meal_name = meal_data.get('name')
        meal_description = meal_data.get('description')
        meal_price = meal_data.get('price')
        meal_image_url = meal_data.get('image_url')
        caterer_id = meal_data.get('caterer_id')

        if not meal_name or not meal_description or not meal_price or not meal_image_url or not caterer_id:
            return jsonify({"message": "Missing required fields"}), 400

        new_meal = Meal(
            name=meal_name,
            description=meal_description,
            price=meal_price,
            image_url=meal_image_url,
            caterer_id=caterer_id
        )

        db.session.add(new_meal)
        db.session.commit()
        return jsonify({"message": "Meal added successfully"})

    elif request.method == 'PUT':
        meal_option_id = request.json.get('meal_option_id')
        new_meal_option_name = request.json.get('new_meal_option')
        if not meal_option_id or not new_meal_option_name:
            return jsonify({"message": "Meal option ID and new name are required"}), 400

        meal_option = Meal.query.get(meal_option_id)
        if meal_option:
            meal_option.name = new_meal_option_name
            db.session.commit()
            return jsonify({"message": "Meal option updated successfully"})
        else:
            return jsonify({"message": "Meal option not found"}), 404

    elif request.method == 'DELETE':
        meal_option_id = request.json.get('meal_option_id')
        if not meal_option_id:
            return jsonify({"message": "Meal option ID is required"}), 400

        meal_option = Meal.query.get(meal_option_id)
        if meal_option:
            db.session.delete(meal_option)
            db.session.commit()
            return jsonify({"message": "Meal option deleted successfully"})
        else:
            return jsonify({"message": "Meal option not found"}), 404


# Get the menu for a specific day
@app.route('/menu/<date>', methods=['GET'])
def get_menu_by_date(date):
    # Parse the date parameter to a Python date object
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"message": "Invalid date format. Please use 'YYYY-MM-DD'."}), 400

    # Query the menu for the specified date
    menu = menu.query.filter_by(day=date_obj).first()

    if not menu:
        return jsonify({"message": f"No menu found for {date}"}), 404

    # Get the meals included in the menu
    menu_meals = menu_meals.query.filter_by(menu_id=menu.id).all()

    # Create a list of meal details for the menu
    menu_items = []
    for menu_meal in menu_meals:
        meal = Meal.query.get(menu_meal.meal_id)
        menu_items.append({
            "meal_id": meal.id,
            "name": meal.name,
            "description": meal.description,
            "price": float(meal.price),  # Convert Decimal to float for JSON serialization
            "image_url": meal.image_url,
        })

    return jsonify({
        "menu_id": menu.id,
        "day": menu.day.strftime('%Y-%m-%d'),
        "menu_items": menu_items,
    })

# Place an order for a meal from the menu
@app.route('/order', methods=['POST'])
@jwt_required()
def place_order():
    current_user = get_jwt_identity()
    user_id = current_user.get('id')

    data = request.json
    meal_id = data.get('meal_id')
    quantity = data.get('quantity')

    if not meal_id or not quantity:
        return jsonify({"message": "Meal ID and quantity are required fields."}), 400

    meal = Meal.query.get(meal_id)

    if not meal:
        return jsonify({"message": "Meal not found."}), 404

    # Calculate the total amount for the order
    total_amount = meal.price * quantity

    # Create the order and add it to the database
    order = Order(
        user_id=user_id,
        meal_id=meal_id,
        quantity=quantity,
        total_amount=total_amount,
    )
    db.session.add(order)
    db.session.commit()

    return jsonify({"message": "Order placed successfully."}), 201

# Changing an order status
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
    
# View all orders
@app.route('/orders', methods=['GET'])
def view_orders():
    orders = Order.query.all()
    orders_list = [order.to_dict() for order in orders]
    return jsonify({"orders": orders_list})

@app.route('/earnings', methods=['GET'])
def view_earnings():
    earnings = calculate_earnings()
    return jsonify({"earnings": earnings})

def calculate_earnings():
    orders = Order.query.all()
    earnings = 0
    for order in orders:
        earnings += order.price

    return earnings

@app.route('/logout', methods=['POST'])
def logout():
    response = jsonify({'Message': "Successfully logged out"})
    unset_jwt_cookies(response)
    return response

if __name__ == "__main__":
    app.run(debug=True, port=5000)