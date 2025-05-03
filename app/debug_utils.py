from wtforms.validators import email

from app import db
from app.models import User, UniversityEmail, Event, Psychologist
import datetime


def reset_db():
    db.drop_all()
    db.create_all()

    users =[
        {'username': 'amy',   'email': 'amy@b.com', 'role': 'Admin', 'pw': 'amy.pw'},
        {'username': 'tom',   'email': 'tom@b.com',                  'pw': 'tom.pw'},
        {'username': 'yin',   'email': 'yin@b.com', 'pw': 'yin.pw'},
        {'username': 'jo',    'email': 'jo@b.com',  'role': 'Organiser', 'pw': 'jo.pw'},
        {'username': 'tan', 'email': 'tan@b.com', 'role': 'Organiser', 'pw': 'tan.pw'}
    ]


    for u in users:
        # get the password value and remove it from the dict:
        pw = u.pop('pw')
        # create a new user object using the parameters defined by the remaining entries in the dict:
        user = User(**u)
        # set the password for the user object:
        user.set_password(pw)
        # add the newly created user object to the database session:
        db.session.add(user)

    university_emails = [
        {'username': 'amy', 'email': 'amy@b.com', 'college':'computer science'},
        {'username': 'tom', 'email': 'tom@b.com', 'college':'computer science'},
        {'username': 'yin', 'email': 'yin@b.com', 'college':'computer science'},
        {'username': 'jo', 'email': 'jo@b.com', 'college':'computer science'},
        {'username': 'tan', 'email': 'tan@b.com', 'college':'computer science'},
        {'username': 'ricky', 'email': 'hxl609@student.bham.ac.uk', 'college': 'computer science'}
    ]

    for e in university_emails:
        email = UniversityEmail(**e)
        db.session.add(email)
    university_events = [
        {
            'title': 'Mindfulness Workshop',
            'text': 'A guided session on mindfulness and meditation techniques to help reduce stress and improve focus.',
            'username': 'jo',
            'date': '10-05-2025',
            'start_time': '09-00',
            'end_time': '10-30',
            'address': 'Room 201, Murray Learning Centre'
        },
        {
            'title': 'Mental Health Open Forum',
            'text': 'A safe, student-led discussion space to share experiences and talk about mental health challenges on campus.',
            'username': 'jo',
            'date': '11-05-2025',
            'start_time': '14-00',
            'end_time': '15-30',
            'address': 'Lecture Theatre A, Arts Building'
        },
        {
            'title': 'De-Stress with Therapy Dogs',
            'text': 'Spend time with certified therapy dogs to help relieve anxiety during exam week.',
            'username': 'tan',
            'date': '12-05-2025',
            'start_time': '13-00',
            'end_time': '14-00',
            'address': 'Ground Floor Lounge, Guild of Students'
        },
        {
            'title': 'Yoga for Mental Clarity',
            'text': 'An outdoor yoga session focusing on breathing and movement for emotional balance.',
            'username': 'tan',
            'date': '13-05-2025',
            'start_time': '08-30',
            'end_time': '09-30',
            'address': 'Green Heart Lawn, Main Campus'
        },
        {
            'title': 'Sleep and Self-Care Talk',
            'text': 'A guest speaker event on the importance of sleep hygiene and building sustainable self-care habits.',
            'username': 'tan',
            'date': '13-05-2025',
            'start_time': '16-00',
            'end_time': '17-00',
            'address': 'Room G15, Alan Walters Building'
        },
        {
            'title': 'Art for the Mind',
            'text': 'A creative workshop where students can express emotions through painting and drawing.',
            'username': 'jo',
            'date': '14-05-2025',
            'start_time': '11-00',
            'end_time': '13-00',
            'address': 'Art Studio 3, Barber Institute of Fine Arts'
        },
        {
            'title': 'Mental Health First Aid Training',
            'text': 'Learn how to identify, understand, and respond to signs of mental illnesses and substance use disorders.',
            'username': 'tan',
            'date': '15-05-2025',
            'start_time': '10-00',
            'end_time': '14-00',
            'address': 'Room 109, Muirhead Tower'
        },
        {
            'title': 'Positive Psychology Seminar',
            'text': 'An academic look into happiness, gratitude, and resilience with practical tips for students.',
            'username': 'jo',
            'date': '15-05-2025',
            'start_time': '15-00',
            'end_time': '16-30',
            'address': 'Lecture Room 4, Frankland Building'
        },
        {
            'title': 'Nature Walk and Reflection',
            'text': 'Join a group walk in the local park followed by a short journaling session to reconnect with yourself.',
            'username': 'tan',
            'date': '16-05-2025',
            'start_time': '08-00',
            'end_time': '09-30',
            'address': 'Start at West Gate, Winterbourne Gardens'
        },
        {
            'title': 'Coping Skills 101',
            'text': 'An interactive event focused on building everyday coping mechanisms for stress, anxiety, and burnout.',
            'username': 'jo',
            'date': '17-05-2025',
            'start_time': '12-00',
            'end_time': '13-30',
            'address': 'Room 305, School of Education'
        }
    ]

    for event in university_events:
        e = Event(**event)
        db.session.add(e)

    psychologists = [
        {
            'username': 'alex',
            'email': 'alex@b.com',
            'availability': 'Available',
            'pw': 'alex_pw'
        },
        {
            'username': 'beth',
            'email': 'beth@b.com',
            'availability': 'Available',
            'pw': 'beth_pw'
        },
        {
            'username': 'carl',
            'email': 'carl@b.com',
            'availability': 'Unavailable',
            'pw': 'carl_pw'
        }
    ]

    for p in psychologists:
        pw = p.pop('pw')
        psy = Psychologist(**p)
        psy.set_password(pw)
        db.session.add(psy)

    db.session.commit()
