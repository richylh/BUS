import pytest
from flask import session, url_for
from app import app, db
from app.models import User
import sqlalchemy as sa


# Positive test: Test the valid login process
def test_valid_login(test_client, test_database):
    with app.app_context():
        user = User(username='testuser', email='test@example.com')
        user.set_password('Test@123')
        db.session.add(user)
        db.session.commit()
    
    response = test_client.post('/login', data={
        'username': 'testuser',
        'password': 'Test@123',
        'remember_me': False,
        'submit': True
    }, follow_redirects=True)
    assert response.status_code == 200

    with test_client.session_transaction() as sess:
        assert '_user_id' in sess
    
    test_client.get('/logout', follow_redirects=True)
    

# Negative test: Test the invalid login process
def test_invalid_login(test_client, test_database):
    with app.app_context():
        user = User(username='testuser', email='test@example.com')
        user.set_password('Test@123')
        db.session.add(user)
        db.session.commit()
    
    response = test_client.post('/login', data={
        'username': 'nonexistentuser',
        'password': 'Test@123',
        'remember_me': False,
        'submit': True
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid username or password' in response.data
    
    response = test_client.post('/login', data={
        'username': 'testuser',
        'password': 'WrongPassword',
        'remember_me': False,
        'submit': True
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid username or password' in response.data
    
