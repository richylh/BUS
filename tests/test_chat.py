import pytest
from flask import session, url_for
from app import app, db
from app.models import User
import sqlalchemy as sa


# Positive test: Test the valid process of sending a message and receiving a reply
def test_valid_chat_message(test_client, test_database, monkeypatch):
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
    
    response = test_client.get('/chat')
    assert response.status_code == 200
    assert b'Chat' in response.data
    
    class MockResponse:
        def __init__(self):
            self.text = "This is a mock AI response"
    
    def mock_generate_content(*args, **kwargs):
        return MockResponse()
    
    class MockClient:
        class Models:
            def generate_content(self, *args, **kwargs):
                return MockResponse()
        
        def __init__(self, *args, **kwargs):
            self.models = self.Models()
    
    import google.genai as genai
    monkeypatch.setattr(genai, 'Client', MockClient)
    
    response = test_client.post('/chat', 
                              json={'message': 'Hello, this is a test message'}, 
                              content_type='application/json')
    
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'response' in json_data
    assert json_data['response'] == "This is a mock AI response"
    

# Negative test: Test the invalid process of sending an empty message
def test_empty_chat_message(test_client, test_database):
    with app.app_context():
        user = User(username='testuser2', email='test2@example.com')
        user.set_password('Test@123')
        db.session.add(user)
        db.session.commit()
    
    response = test_client.post('/login', data={
        'username': 'testuser2',
        'password': 'Test@123',
        'remember_me': False,
        'submit': True
    }, follow_redirects=True)
    assert response.status_code == 200
    
    with test_client.session_transaction() as sess:
        assert '_user_id' in sess
    
    response = test_client.get('/chat')
    assert response.status_code == 200
    
    response = test_client.post('/chat', 
                              json={'message': ''}, 
                              content_type='application/json')
    
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'response' in json_data
    
