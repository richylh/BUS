from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask_login import UserMixin
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login
from dataclasses import dataclass
import datetime

@dataclass
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    role: so.Mapped[str] = so.mapped_column(sa.String(10), default="Normal")
    events: so.Mapped[list['Event']] = relationship(back_populates='user', cascade='all, delete-orphan')
    appointments: so.Mapped[list['Appointment']] = relationship(back_populates='user', cascade='all, delete-orphan')
    logs: so.Mapped[list['BookingLog']] = relationship(back_populates='user', cascade='all, delete-orphan')
    enrollments: so.Mapped[list['Enrollment']] = relationship(back_populates='user', cascade='all, delete-orphan')
    user_type: Mapped[str] = so.mapped_column(sa.String(64), default="user")
    __mapper_args__ = {
        "polymorphic_identity": "user",
        "polymorphic_on": user_type
    }


    def __repr__(self):
        pwh= 'None' if not self.password_hash else f'...{self.password_hash[-5:]}'
        return f'User(id={self.id}, username={self.username}, email={self.email}, role={self.role}, pwh={pwh})'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Psychologist(User):
    __tablename__ = 'Psychologist'
    id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('users.id'), primary_key=True)
    availability: so.Mapped[str] = so.mapped_column(sa.String(64), default="Available")
    #appointment: so.Mapped[str] = so.mapped_column(sa.String(64), default="Unbooked")

    __mapper_args__ = {
        "polymorphic_identity": "Psychologist",
    }

@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))


class Event(db.Model):
    __tablename__ = 'events'

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    title: so.Mapped[str] = so.mapped_column(sa.String(64), unique=True)
    text: so.Mapped[str] = so.mapped_column(sa.String(3200))
    #user_id: so.Mapped[int] = so.mapped_column(ForeignKey('users.id'), index=True)
    username: so.Mapped[str] = so.mapped_column(ForeignKey('users.username'), index=True)
    user: so.Mapped['User'] = relationship(back_populates='events')
    status: so.Mapped[str] = so.mapped_column(sa.String(64),default='Open')
    date: so.Mapped[str] = so.mapped_column(sa.String(64),default='None')
    start_time: so.Mapped[str] = so.mapped_column(sa.String(64),default='None')
    end_time: so.Mapped[str] = so.mapped_column(sa.String(64),default='None')
    address: so.Mapped[str] = so.mapped_column(sa.String(256))






class Enrollment(db.Model):
    __tablename__ = 'enrollments'

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    title: so.Mapped[str] = so.mapped_column(sa.String(64))
    #user_id: so.Mapped[int] = so.mapped_column(ForeignKey('users.id'), index=True)
    username: so.Mapped[str] = so.mapped_column(ForeignKey('users.username'), index=True)
    user: so.Mapped['User'] = relationship(back_populates='enrollments')
    status: so.Mapped[str] = so.mapped_column(sa.String(64),default='Open')
    date: so.Mapped[str] = so.mapped_column(sa.String(64),default='None')
    start_time: so.Mapped[str] = so.mapped_column(sa.String(64),default='None')
    end_time: so.Mapped[str] = so.mapped_column(sa.String(64),default='None')
    address: so.Mapped[str] = so.mapped_column(sa.String(256))

    def to_dict(self):
        return {
            'id': self.id,
            'title':self.title,
            'username': self.username
        }







class Appointment(db.Model):
    __tablename__ = 'appointments'
    new_id: so.Mapped[int] = so.mapped_column(primary_key=True)
    id: so.Mapped[int] = so.mapped_column(sa.String(64))
    date: so.Mapped[str] = so.mapped_column(sa.String(64))
    weekday: so.Mapped[str] = so.mapped_column(sa.String(16))
    slot: so.Mapped[str] = so.mapped_column(sa.String(64))
    user_id: so.Mapped[int] = so.mapped_column(ForeignKey('users.id'), index=True, unique=True)
    user: so.Mapped['User'] = relationship(back_populates='appointments')
    user_name: so.Mapped[str] = so.mapped_column(sa.String(64))

    # status: so.Mapped[str] = so.mapped_column(sa.String(64), default='Open')

class UniversityEmail(db.Model):
    __tablename__ = 'university_emails'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64))
    college: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))

class BookingLog(db.Model):
    __tablename__ = 'logs'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    date: so.Mapped[str] = so.mapped_column(sa.String(64))
    weekday: so.Mapped[str] = so.mapped_column(sa.String(16))
    slot: so.Mapped[str] = so.mapped_column(sa.String(64))
    user_id: so.Mapped[int] = so.mapped_column(ForeignKey('users.id'), index=True, unique=True)
    user: so.Mapped['User'] = relationship(back_populates='logs')

