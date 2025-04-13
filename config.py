import os

basedir = os.path.abspath(os.path.dirname(__file__))
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or b'WR#&f&+%78er0we=%799eww+#7^90-;s'

    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'data', 'uploads')
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024

    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app', 'data', 'data.sqlite')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True

    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'electriccurtaintrack@gmail.com'
    MAIL_PASSWORD = 'yjpdc02!'
