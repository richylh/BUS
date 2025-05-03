from random import choices

from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import SubmitField, HiddenField, StringField, PasswordField, BooleanField, SelectField, IntegerField
#from wtforms.fields.numeric import IntegerField
from wtforms.fields.simple import TextAreaField
from wtforms.validators import DataRequired, EqualTo, NumberRange, ValidationError, Email, Optional, Length, Regexp, AnyOf
from app import db
from app.models import User
import datetime

def password_policy(form, field):
    message = """A password must be at least 8 characters long, and have an
                uppercase and lowercase letter, a digit, and a character which is
                neither a letter or a digit"""
    if len(field.data) < 8:
        raise ValidationError(message)
    flg_upper = flg_lower = flg_digit = flg_non_let_dig = False
    for ch in field.data:
        flg_upper = flg_upper or ch.isupper()
        flg_lower = flg_lower or ch.islower()
        flg_digit = flg_digit or ch.isdigit()
        flg_non_let_dig = flg_non_let_dig or not ch.isalnum()
    if not (flg_upper and flg_lower and flg_digit and flg_non_let_dig):
        raise ValidationError(message)

class ChooseForm(FlaskForm):
    choice = HiddenField('Choice')
    appo_id = HiddenField('appo_id')
    user_id = HiddenField('user_id')
    current_choice = HiddenField()

class LoginForm(FlaskForm):
    username = StringField('Username or Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class ChangePasswordForm(FlaskForm):
    password = PasswordField('Current Password',validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(),password_policy])
    confirm_password = PasswordField('Confirm New Password',validators=[DataRequired(),EqualTo('new_password')])
    submit = SubmitField('Change Password')

    @staticmethod
    def validate_password(form, field):
        if not current_user.check_password(field.data):
            raise ValidationError('Incorrect Password')

class ChangeEmailForm(FlaskForm):
    password = PasswordField('Your Password',validators=[DataRequired()])
    new_email = StringField('New Email', validators=[DataRequired()])
    confirm_email = StringField('Confirm New Email',validators=[DataRequired(),EqualTo('new_email')])
    submit = SubmitField('Update Email')

class RegisterForm(FlaskForm):
    username = StringField('Username',validators=[DataRequired()])
    email = StringField('Email',validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(),password_policy])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    @staticmethod
    def validate_username(form, field):
        q = db.select(User).where(User.username==field.data)
        if db.session.scalar(q):
            raise ValidationError('Username already taken. Try again')

    def validate_email(form, field):
        q = db.select(User).where(User.email==field.data)
        if db.session.scalar(q):
            raise ValidationError('Email already taken. Try again')

class RegisterEmail(FlaskForm):
    email = StringField('Your University Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Verify Email')

class RegisterEmailVerify(FlaskForm):
    email = StringField('Your University Email', validators=[DataRequired(), Email()])
    verify = StringField('Verification Code', validators=[DataRequired()])
    submit = SubmitField('Verify')

class EventsForm(FlaskForm):
    edit = HiddenField(default='-1')
    title = StringField('Event Title', validators=[DataRequired()])
    text = TextAreaField('Event information', validators=[DataRequired()])
    date = StringField('Date (dd-mm-yyyy)', validators= [Regexp(r'^\d{2}-\d{2}-\d{4}$', message = "Date must be in format dd-mm-yyyy")])
    start_time = StringField('Start (hh-mm)', validators= [Regexp(r'^\d{2}-\d{2}$', message = "Start time must be in format hh-mm")])
    end_time = StringField('End (hh-mm)', validators= [Regexp(r'^\d{2}-\d{2}$', message = "End time must be in format hh-mm")])
    status = StringField('Status (Open or Closed)', validators=[AnyOf(values=["Open","Closed"], message= "Status must be either 'Open' or 'Closed'")])
    address = StringField("Address", validators=[DataRequired()])
    submit = SubmitField('Publish Event')