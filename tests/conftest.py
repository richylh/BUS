import pytest
from app import app, db
from app.models import UniversityEmail

@pytest.fixture(scope='session')
def app_context():
    with app.app_context():
        yield

@pytest.fixture(scope='function')
def test_client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

@pytest.fixture(scope='function')
def test_database():
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='function')
def test_university_email(test_database):
    test_email = UniversityEmail(email='test@university.edu', username='testuser')
    test_database.session.add(test_email)
    test_database.session.commit()
    return test_email