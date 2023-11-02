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

# Sign up====working 
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = request.json['username']
    email = request.json['email']
    password = request.json['password']
    role = request.json['role']

    if not username or not email or not password:
        return jsonify({"Message": "Missing required fields"})

    user_exists = User.query.filter_by(username=username).first() is not None

    if user_exists:
        return jsonify({"message": "Username already exists"}), 409
    
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, email=email, password=hashed_password, role=role)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message':'Signed up successfully'}), 201

# Login route====working
@app.route('/login', methods=['POST'])
def login():
    auth = request.json
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
            "expires": datetime.utcnow() + timedelta(days=7)
        }, app.config['SECRET_KEY'])
        return jsonify({
            "access token": token,
            "message":"Logged in successfully"
        })

    return make_response(
        'Could not verify',
        403,
        {'WWW-Authenticate': 'Basic realm = "Wrong password"'}

     )


# get all users
@app.route('/users', methods=['GET'])
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
@app.route('/users/<int:user_id>', methods=['GET'])
def get_user_by_id(user_id):
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

# @app.route('/profile/<username>', methods=['GET'])
# @jwt_required()
# def user_profile(username):
#     print(username)
#     if not username:
#         return jsonify({'No username found!'}), 404
    
#     user = User.query.filter_by(username=username).first()
#     print('user foun is:', user)

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
            'name': caterer.name,
            'created_at': caterer.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': caterer.updated_at.strftime('%Y-%m-%d %H:%M:%S') if caterer.updated_at else None
        }
        caterers_info.append(caterer_info)

    return jsonify(caterers_info)

# @app.route('/caterer/info', methods=['GET'])
# @jwt_required()
# def get_caterer_info():
#     current_user = get_jwt_identity()
#     caterer = Caterer.query.filter_by(user_id=current_user['id']).first()

#     if not caterer:
#         return jsonify({'message': 'Caterer not found'}), 404

#     response_body = {
#         'name': caterer.name,
#         'star_meal': caterer.star_meal,
#         'created_at': caterer.created_at,
#         'updated_at': caterer.updated_at
#     }

#     return jsonify(response_body)

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
        return jsonify({"access_token": token})

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
def manage_meal_options():
    if request.method == 'GET':
        meal_options = Meal.query.all()
        meal_options_list = [meal_option.to_dict() for meal_option in meal_options]
        return jsonify({"meal options": meal_options_list})
    
    elif request.method == 'POST':
        meal_option_name = request.json.get('meal_option')
        new_meal_option = Meal(name=meal_option_name)
        db.session.add(new_meal_option)
        db.session.commit()
        return jsonify({"message": "Meal option added successfully"})
    
    elif request.method == 'PUT':
        meal_option_id = request.json.get('meal_option_id')
        new_meal_option_name= request.json.get('new_meal_option')
        meal_option = Meal.query.get(meal_option_id)
        if meal_option:
            meal_option.name = new_meal_option_name
            db.session.commit()
            return jsonify({"message": "Meal option updated successfully"})
        else:
            return jsonify({"message": "Meal option not found"})
        
    elif request.method == 'DELETE':
        meal_option_id = request.json.get('meal_option_id')
        meal_option = Meal.query.get(meal_option_id)
        if meal_option:
            db.session.delete(meal_option)
            db.session.commit()
            return jsonify({"message": "Meal option deleted successfully"})
        else:
            return jsonify({"message": "Meal option not found"})
    
@app.route('/menu/<date>', methods=['POST'])
def set_menu(date):
    menu_items = request.json.get('menu_items')
    menu = Meal(date=date, items=menu_items)
    db.session.add(menu)
    db.session.commit()
    return jsonify({"message": f"Menu set successfully for {date}"})

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
    app.run(debug=True, port=5555)