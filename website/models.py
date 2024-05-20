from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func


class Educator(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    role = db.Column(db.String(50))
    date_created = db.Column(db.Date(), default=func.now())
    sessions = db.relationship('Sessions')

class Coordinator(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    role = db.Column(db.String(50))
    date_created = db.Column(db.Date(), default=func.now())


class Sessions(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)

    # relationship between educator id and emotion results for each educator
    user_id = db.Column(db.Integer, db.ForeignKey('educator.id'), unique=True)

    title = db.Column(db.String(100), nullable=False)
    interested = db.Column(db.Integer, nullable=False)
    uninterested = db.Column(db.Integer, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date(), default=func.now())

