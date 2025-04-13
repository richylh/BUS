from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask_login import UserMixin
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
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
    appointments: so.Mapped[list['Appoitment']] = relationship(back_populates='user', cascade='all, delete-orphan')

    def __repr__(self):
        pwh= 'None' if not self.password_hash else f'...{self.password_hash[-5:]}'
        return f'User(id={self.id}, username={self.username}, email={self.email}, role={self.role}, pwh={pwh})'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))


class Event(db.Model):
    __tablename__ = 'events'

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    event_name: so.Mapped[str] = so.mapped_column(sa.String(64))
    description: so.Mapped[str] = so.mapped_column(sa.String(1024))
    event_datetime: so.Mapped[datetime] = so.mapped_column(sa.DateTime)
    user_id: so.Mapped[int] = so.mapped_column(ForeignKey('users.id'), index=True)
    user: so.Mapped['User'] = relationship(back_populates='events')
    status: so.Mapped[str] = so.mapped_column(sa.String(64),default='Open')


class Appoitment(db.Model):
    __tablename__ = 'appointments'

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    appointment_name: so.Mapped[str] = so.mapped_column(sa.String(64))
    description: so.Mapped[str] = so.mapped_column(sa.String(1024))
    app_datetime: so.Mapped[datetime] = so.mapped_column(sa.DateTime)
    user_id: so.Mapped[int] = so.mapped_column(ForeignKey('users.id'), index=True)
    user: so.Mapped['User'] = relationship(back_populates='appointments')
    status: so.Mapped[str] = so.mapped_column(sa.String(64), default='Open')


class UniversityEmail(db.Model):
    __tablename__ = 'university_emails'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64))
    college: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))