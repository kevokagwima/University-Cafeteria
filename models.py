from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import UserMixin

db = SQLAlchemy()
bcrypt = Bcrypt()

class Admin(db.Model, UserMixin):
  __tablename__ = 'Admin'
  id = db.Column(db.Integer(), primary_key=True)
  email = db.Column(db.String(50), nullable=False)
  phone_number = db.Column(db.Integer(), nullable=False)
  account_type = db.Column(db.String(10), default="Admin")
  password = db.Column(db.String(80), nullable=False)

class Student(db.Model, UserMixin):
  __tablename__ = 'Student'
  id = db.Column(db.Integer(), primary_key=True)
  regno = db.Column(db.Integer(), nullable=False)
  first_name = db.Column(db.String(30), nullable=False)
  last_name = db.Column(db.String(30), nullable=False)
  phone_number = db.Column(db.Integer(), nullable=False)
  email = db.Column(db.String(50), nullable=False)
  password = db.Column(db.String(80), nullable=False)
  account_type = db.Column(db.String(10), default="Student")

  @property
  def passwords(self):
    return self.passwords

  @passwords.setter
  def passwords(self, plain_text_password):
    self.password = bcrypt.generate_password_hash(plain_text_password).decode("utf-8")

  def check_password_correction(self, attempted_password):
    return bcrypt.check_password_hash(self.password, attempted_password)

class Meals(db.Model):
  __tablename__ = 'Meals'
  id = db.Column(db.Integer(), primary_key=True)
  ref_no = db.Column(db.Integer(), nullable=False)
  name = db.Column(db.String(50), nullable=False)
  category = db.Column(db.String(20), nullable=False)
  price = db.Column(db.Integer(), nullable=False, default=0)
  order_item = db.relationship("Order_item", backref="order-item", lazy=True)

class Order(db.Model):
  __tablename__ = 'Orders'
  id = db.Column(db.Integer(), primary_key=True)
  order_id = db.Column(db.Integer(), nullable=False)
  order_items = db.relationship("Order_item", backref="order-meal", lazy=True)
  user = db.Column(db.Integer(), nullable=False)
  placed = db.Column(db.Boolean(), default=False)
  confirmed = db.Column(db.Boolean(), default=False)
  date = db.Column(db.DateTime())
  status = db.Column(db.String(10), default="Active", nullable=False)

class Order_item(db.Model):
  __tablename__ = 'Order_items'
  id = db.Column(db.Integer(), primary_key=True)
  order = db.Column(db.Integer(), db.ForeignKey('Orders.id'))
  meal = db.Column(db.Integer(), db.ForeignKey('Meals.id'))
  user = db.Column(db.Integer(), nullable=False)
