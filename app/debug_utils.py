from wtforms.validators import email

from app import db
from app.models import User, UniversityEmail
import datetime


def reset_db():
    db.drop_all()
    db.create_all()

    users =[
        {'username': 'amy',   'email': 'amy@b.com', 'role': 'Admin', 'pw': 'amy.pw'},
        {'username': 'tom',   'email': 'tom@b.com',                  'pw': 'tom.pw'},
        {'username': 'yin',   'email': 'yin@b.com', 'role': 'Admin', 'pw': 'yin.pw'},
        {'username': 'jo',    'email': 'jo@b.com',  'role': 'Organiser', 'pw': 'jo.pw'}
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
        {'username': 'ricky', 'email': 'hxl609@student.bham.ac.uk', 'college': 'computer science'}
    ]

    for e in university_emails:
        email = UniversityEmail(**e)
        db.session.add(email)

    db.session.commit()
