import pytest
from flask import session, url_for
from app import app, db
from app.models import User, Appointment, Psychologist, BookingLog
import sqlalchemy as sa
import datetime


# Positive test: Test the valid process of booking an appointment
def test_valid_appointment(test_client, test_database, monkeypatch):
    class MockChooseForm:
        def __init__(self):
            self.choice = None
        
        def csrf_token(self):
            return ''
    
    from flask import render_template as original_render
    
    def mock_render_template(*args, **kwargs):
        if args and args[0] == 'appointment.html':
            kwargs['form'] = MockChooseForm()
        return original_render(*args, **kwargs)
    
    monkeypatch.setattr('flask.render_template', mock_render_template)
    with app.app_context():
        user = User(username='testuser', email='test@example.com', user_type="user", role="Normal")
        user.set_password('Test@123')
        db.session.add(user)
        
        psychologist = User(username='psychdoctor', email='psych@example.com', user_type="Psychologist")
        psychologist.set_password('Test@123')
        db.session.add(psychologist)
        db.session.commit()
        
        db.session.execute(sa.insert(Psychologist.__table__).values(id=psychologist.id))
        
        today = datetime.datetime.today().date()
        date_str = today.strftime('%Y-%m-%d')
        slot = '09:00'
        weekday = today.strftime('%A')
        
        booking_log = BookingLog(
            date=date_str,
            weekday=weekday,
            slot=slot,
            user_id=user.id
        )
        db.session.add(booking_log)
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
    
    response = test_client.get('/appointments')
    assert response.status_code == 200
    assert b'Appointment' in response.data
    
    response = test_client.post('/book_an_appointment/2', follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Book successful' in response.data
    assert b'testuser' in response.data
    
    with app.app_context():
        appointment = db.session.scalar(
            sa.select(Appointment).where(Appointment.user_id == 1)
        )
        assert appointment is not None
        assert appointment.user.username == 'testuser'


# Negative test: Test the invalid process of booking an invalid appointment
def test_invalid_appointment(test_client, test_database, monkeypatch):
    class MockChooseForm:
        def __init__(self):
            self.choice = None
        
        def csrf_token(self):
            return ''
    
    from flask import render_template as original_render
    
    def mock_render_template(*args, **kwargs):
        if args and args[0] == 'appointment.html':
            kwargs['form'] = MockChooseForm()
        return original_render(*args, **kwargs)
    
    monkeypatch.setattr('flask.render_template', mock_render_template)
    
    user1_id = None
    user2_id = None
    psychologist_id = None
    
    with app.app_context():
        db.session.execute(sa.delete(Appointment))
        
        user1 = User(username='user1', email='user1@example.com', user_type="user", role="Normal")
        user1.set_password('Test@123')
        user2 = User(username='user2', email='user2@example.com', user_type="user", role="Normal")
        user2.set_password('Test@123')
        
        psychologist = User(username='psychdoctor', email='psych@example.com', user_type="Psychologist")
        psychologist.set_password('Test@123')
        
        db.session.add(user1)
        db.session.add(user2)
        db.session.add(psychologist)
        db.session.commit()
        
        user1_id = user1.id
        user2_id = user2.id
        psychologist_id = psychologist.id
        
        db.session.execute(sa.insert(Psychologist.__table__).values(id=psychologist.id))
        
        today = datetime.datetime.today().date()
        date_str = today.strftime('%Y-%m-%d')
        slot = '09:00'
        weekday = today.strftime('%A')
        
        booking_log = BookingLog(
            date=date_str,
            weekday=weekday,
            slot=slot,
            user_id=user1.id
        )
        db.session.add(booking_log)
        
        appointment = Appointment(
            id=psychologist_id,
            user_id=user1_id,
            date=date_str,
            weekday=weekday,
            slot=slot,
            user_name=user1.username
        )
        db.session.add(appointment)
        db.session.commit()
    
    response = test_client.post('/login', data={
        'username': 'user2',
        'password': 'Test@123',
        'remember_me': False,
        'submit': True
    }, follow_redirects=True)
    assert response.status_code == 200

    response = test_client.get('/appointments')
    assert response.status_code == 200
    
    response = test_client.post(f'/book_an_appointment/{psychologist_id}', follow_redirects=True)
    
    assert response.status_code == 200
    

    with app.app_context():
        appointment = db.session.scalar(
            sa.select(Appointment).where(Appointment.user_id == user2_id)
        )
        assert appointment is None
        
        appointment1 = db.session.scalar(
            sa.select(Appointment).where(Appointment.user_id == user1_id)
        )
        assert appointment1 is not None
