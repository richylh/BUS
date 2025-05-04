import pytest
from flask import session, url_for
from app import app, db
from app.models import User, UniversityEmail
import sqlalchemy as sa


# Positive test: Test the valid registration process
def test_valid_registration(test_client, test_database, test_university_email):
    response = test_client.get('/register_email')
    assert response.status_code == 200
    
    response = test_client.post('/register_email', data={
        'email': 'test@university.edu',
        'submit': True
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Verification code' in response.data
    
    with test_client.session_transaction() as sess:
        verify_code = sess['verify_code']
        email = sess['email']
    
    response = test_client.post('/register_verify', data={
        'email': email,
        'verify': verify_code,
        'submit': True
    }, follow_redirects=True)
    assert response.status_code == 200
    
    response = test_client.post('/register', data={
        'username': 'testuser',
        'email': email,
        'password': 'Test@123',
        'confirm_password': 'Test@123',
        'submit': True
    }, follow_redirects=True)
    assert response.status_code == 200
    
    with app.app_context():
        user = db.session.scalar(sa.select(User).where(User.email == email))
        assert user is not None
        assert user.username == 'testuser'
        assert user.check_password('Test@123')


# Negative test: Test the invalid registration process
def test_invalid_registration(test_client, test_database, test_university_email):
    response = test_client.post('/register_email', data={
        'email': 'nonexistent@example.com',
        'submit': True
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Email not found' in response.data
    
    response = test_client.post('/register_email', data={
        'email': 'test@university.edu',
        'submit': True
    }, follow_redirects=True)
    
    response = test_client.post('/register_verify', data={
        'email': 'test@university.edu',
        'verify': '000000',
        'submit': True
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Verification code not correct' in response.data
    
    with app.app_context():
        existing_user = User(username='existinguser', email='existing@example.com')
        existing_user.set_password('Password@123')
        db.session.add(existing_user)
        db.session.commit()
    
    with test_client.session_transaction() as sess:
        sess['email'] = 'test@university.edu'
        sess['verify_code'] = '123456'
    
    response = test_client.post('/register_verify', data={
        'email': 'test@university.edu',
        'verify': '123456',
        'submit': True
    }, follow_redirects=True)
    
    response = test_client.post('/register', data={
        'username': 'existinguser',
        'email': 'test@university.edu',
        'password': 'Test@123',
        'confirm_password': 'Test@123',
        'submit': True
    })
    assert b'Username already taken' in response.data