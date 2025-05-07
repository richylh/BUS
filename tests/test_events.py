import pytest
from flask import session, url_for
from app import app, db
from app.models import User, Event, Enrollment
import sqlalchemy as sa


# Positive test: Test the valid process of adding an event by the organiser
def test_organiser_add_event(test_client, test_database, monkeypatch):
    with app.app_context():
        user = User(username='organiser', email='organiser@example.com', role='Organiser')
        user.set_password('Test@123')
        db.session.add(user)
        db.session.commit()
    
    response = test_client.post('/login', data={
        'username': 'organiser',
        'password': 'Test@123',
        'remember_me': False,
        'submit': True
    }, follow_redirects=True)
    assert response.status_code == 200
    
    with test_client.session_transaction() as sess:
        assert '_user_id' in sess
    
    event_data = {
        'edit': '-1',
        'title': 'Test Event',
        'text': 'This is a test event description',
        'date': '01-12-2023',
        'start_time': '10-00',
        'end_time': '12-00',
        'status': 'Open',
        'address': 'Test Address',
        'submit': True
    }
    
    class MockChooseForm:
        def __init__(self):
            self.choice = None
            self.current_choice = None
        
        def csrf_token(self):
            return ''
    
    from flask import render_template as original_render
    
    def mock_render_template(*args, **kwargs):
        if args and args[0] == 'manager.html':
            kwargs['choose_form'] = MockChooseForm()
        return original_render(*args, **kwargs)
    
    monkeypatch.setattr('flask.render_template', mock_render_template)
    
    response = test_client.post('/manager', data=event_data, follow_redirects=True)
    assert response.status_code == 200
    
    with app.app_context():
        event = db.session.scalar(sa.select(Event).where(Event.title == 'Test Event'))
        assert event is not None
        assert event.title == 'Test Event'
        assert event.text == 'This is a test event description'
        assert event.username == 'organiser'
        assert event.status == 'Open'
        assert event.date == '01-12-2023'
        assert event.start_time == '10-00'
        assert event.end_time == '12-00'
        assert event.address == 'Test Address'


# Negative test: Test the invalid process of enrolling for the same event twice by a user
def test_user_enroll_twice(test_client, test_database):
    with app.app_context():
        user = User(username='normaluser', email='normal@example.com', role='Normal')
        user.set_password('Test@123')
        db.session.add(user)
        db.session.commit()
        
        event = Event(
            title='Enrollment Test Event',
            text='This is an event for testing enrollment',
            username='normaluser',
            status='Open',
            date='01-12-2023',
            start_time='14-00',
            end_time='16-00',
            address='Test Address'
        )
        db.session.add(event)
        db.session.commit()
    
    response = test_client.post('/login', data={
        'username': 'normaluser',
        'password': 'Test@123',
        'remember_me': False,
        'submit': True
    }, follow_redirects=True)
    assert response.status_code == 200
    
    with app.app_context():
        event = db.session.scalar(sa.select(Event).where(Event.title == 'Enrollment Test Event'))
        event_id = event.id
    
    response = test_client.get(f'/enrollment/{event_id}', follow_redirects=True)
    assert response.status_code == 200
    assert b'Successfully enrolled in the event!' in response.data
    
    with app.app_context():
        enrollment = db.session.scalar(
            sa.select(Enrollment).where(
                (Enrollment.title == 'Enrollment Test Event') & 
                (Enrollment.username == 'normaluser')
            )
        )
        assert enrollment is not None
    
    response = test_client.get(f'/enrollment/{event_id}', follow_redirects=True)
    assert response.status_code == 200
    assert b'Already enrolled in the event' in response.data
    
