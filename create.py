from flask import Flask
from models import *
import csv, random

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
db.init_app(app)

def main():
  db.create_all()

def meal():
  f = open("data.csv")
  reader = csv.reader(f)
  meals = Meals.query.all()
  meal_name = []
  for meal in meals:
    meal_name.append(meal.name)
  for name,category,price in reader:
    if name in meal_name:
      pass
    else:
      new_meal = Meals(
        name=name,
        category=category,
        price=price,
        ref_no=random.randint(100000,999999)
      )
      db.session.add(new_meal)
      db.session.commit()
      print(f'{new_meal.name} addedd')

def add_admin():
  new_admin = Admin(
    email="admin@gmail.com",
    password="admin",
    phone_number="0700256984"
  )
  db.session.add(new_admin)
  db.session.commit()
  print("Admin addedd")

if __name__ == '__main__':
  with app.app_context():
    main()
    meal()
    add_admin()
