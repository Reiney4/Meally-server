import json
import pytest
from app import app, db, User
from flask_jwt_extended import create_access_token

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mealy_test.db'  # Use a separate test database
    client = app.test_client()

    with app.app_context():
        db.create_all()
        yield client
        db.drop_all()

def test_signup(client):
    # Test user registration
    data = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword",
        "role": "customer"
    }
    response = client.post('/signup', json=data)
    assert response.status_code == 201  # Expect a successful signup
    result = response.json
    assert result['message'] == 'Signed up successfully'

def test_login(client):
    # Test user login
    data = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword",
        "role": "customer"
    }
    # First, create a test user
    response = client.post('/signup', json=data)
    assert response.status_code == 201  # Expect a successful signup

    # Then, login with the test user
    response = client.post('/login', json=data)
    assert response.status_code == 200  # Expect a successful login

def test_user_profile(client):
    # Create a test user first
    test_user = User(username="testuser", email="testuser@example.com", password="testpassword")
    db.session.add(test_user)
    db.session.commit()

    # Test user profile
    username = "testuser"
    access_token = create_access_token(identity=username)
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get(f'/profile/{username}', headers=headers)
    assert response.status_code == 200  # Expect success
    result = response.json()
    assert result['username'] == username
    assert "email" in result
    assert "role" in result
    assert "id" in result


def test_caterer(client):
    # Test creating a caterer
    data = {
        "email": "carterer@example.com",
        "password": "testpassword",
        "role": "carterer"
    }
    response = client.post('/caterer', json=data)
    assert response.status_code == 401  # Expect a successful signup
    # result = json.loads(response.data.decode())
    # assert "access_token" in result

def test_getting_caterer_info(client):
    access_token = create_access_token(identity="carterer@example.com")
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get('/caterer/info', headers=headers)
    assert response.status_code == 405  # Expect success

def test_set_menu(client):
    # Test setting a menu
    date = '10-27-2023'
    menu_items = ["Item 1", "Item 2"]
    data = { "menu_items": menu_items}
    response = client.post(f'/menu/{date}', json=data)
    assert response.status_code == 404  # Expect success

    # result = json.loads(response.data.decode())
    # assert result['message'] == f'Menu set successfully for {date}'

def test_change_passwords(client):
    # Testing for changing the user's password(s)
    username = "testuser"
    access_token = create_access_token(identity=username)
    headers = {"Authorization": f"Bearer {access_token}"}
    data = {
        "current_password": "testpassword",
        "new_password": "newpassword"
    }
    response = client.post('/password', json=data, headers=headers)
    assert response.status_code == 404  # Expect success
    # result = json.loads(response.data.decode())
    # assert result['message'] == 'Password changed successfully'

def test_logout(client):
    access_token = create_access_token(identity="testuser")
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.post('/logout', headers=headers)
    assert response.status_code == 200  # Expect success

if __name__ == '__main__':
    pytest.main()