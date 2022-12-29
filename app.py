from flask import Flask, render_template, flash, redirect, url_for, request
from flask_login import login_manager, LoginManager, login_user, logout_user, login_required, current_user
from models import db, Meals, Student, Order, Order_item, Admin
from forms import Registration_form, Login, Admin_Login
from email.message import EmailMessage
import datetime, random, ssl, smtplib, os

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["SECRET_KEY"] = 'sabinaonlinorderproject'

db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = '/sign-in'
login_manager.login_message_category = "danger"
login_manager.init_app(app)
email_sender = os.environ["Email_from"]
email_password = os.environ["Email_password"]
em = EmailMessage()

@login_manager.user_loader
def load_user(user_id):
  try:
    return Admin.query.filter_by(phone_number=user_id).first() or Student.query.filter_by(phone_number=user_id).first()
  except:
    flash(f"Failed to login the user", category="danger")

@app.route("/sign-up", methods=["POST", "GET"])
def sign_up():
  form = Registration_form()
  if form.validate_on_submit():
    new_user = Student(
      regno = random.randint(100000,999999),
      first_name = form.first_name.data,
      last_name = form.last_name.data,
      phone_number = form.phone_number.data,
      email = form.email_address.data,
      passwords = form.password.data
    )
    db.session.add(new_user)
    db.session.commit()
    flash("Registration successfull", category="success")
    try:
      em['sender'] = email_sender
      em['to'] = new_user.email
      em['subject'] = "Account Created Successfully"
      em.set_content("Your student account has been created successfully")
      context = ssl.create_default_context()
      with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.sendmail(email_sender, new_user.email, em.as_string())
        smtp.quit()
        del em["To"]
    except:
      print("email not sent")
    return redirect(url_for('sign_in'))

  return render_template("signup.html", form=form)

@app.route("/sign-in", methods=["POST", "GET"])
def sign_in():
  form = Login()
  if form.validate_on_submit():
    user = Student.query.filter_by(email=form.email_address.data).first()
    if user and user.check_password_correction(attempted_password=form.password.data):
      login_user(user, remember=True)
      flash(f"Login successfull", category="success")
      return redirect(url_for('index'))
    elif user is None:
      flash(f"No user with that email address", category="danger")
      return redirect(url_for('sign_in'))
    else:
      flash(f"Invalid credentials", category="danger")
      return redirect(url_for('sign_in'))

  return render_template("signin.html", form=form)

@app.route("/admin-sign-in", methods=["POST", "GET"])
def admin_sign_in():
  form = Admin_Login()
  if form.validate_on_submit():
    user = Admin.query.filter_by(email=form.email_address.data).first()
    if user and user.password == "admin":
      login_user(user, remember=True)
      flash(f"Login successfull", category="success")
      return redirect(url_for('index'))
    elif user is None:
      flash(f"No user with that email address", category="danger")
      return redirect(url_for('admin_sign_in'))
    else:
      flash(f"Invalid credentials", category="danger")
      return redirect(url_for('admin_sign_in'))

  return render_template("admin.html", form=form)

@login_required
@app.route("/")
@app.route("/home")
def index():
  meals = Meals.query.all()
  if current_user.is_authenticated:
    existing_order = Order.query.filter_by(user=current_user.phone_number, status="Active").first()
    return render_template("index.html", existing_order=existing_order, meals=meals)

  return render_template("index.html", meals=meals)

@login_required
@app.route("/add-to-cart/<int:meal_id>")
def new_order(meal_id):
  existing_order = Order.query.filter_by(user=current_user.phone_number, status="Active").first()
  meal = Meals.query.get(meal_id)
  if existing_order:
    order_items = Order_item.query.filter_by(order=existing_order.id).all()
    order_items_meals = []
    for order_item in order_items:
      order_items_meals.append(order_item.meal)
    if meal_id in order_items_meals:
      flash("Item already in cart", category="warning")
    else:
      new_order_item = Order_item(
        order = existing_order.id,
        meal = meal.id,
        user = current_user.phone_number
      )
      db.session.add(new_order_item)
      db.session.commit()
      flash("Cart Updated", category="success")
  else:
    new_order = Order(
      order_id = random.randint(100000,999999),
      user = current_user.phone_number,
      date = datetime.datetime.now()
    )
    db.session.add(new_order)
    db.session.commit()
    new_order_item = Order_item(
      order = new_order.id,
      meal = meal.id,
      user = current_user.phone_number
    )
    db.session.add(new_order_item)
    db.session.commit()
    flash("Order has been placed", category="success")
  return redirect(url_for('index'))

@login_required
@app.route("/cart")
def cart():
  existing_order = Order.query.filter_by(user=current_user.phone_number, status="Active").first()
  meals = Meals.query.all()
  if existing_order:
    order_items = Order_item.query.filter_by(order=existing_order.id).all()
    return render_template("cart.html", existing_order=existing_order, meals=meals, order_items=order_items)

  return render_template("cart.html")

@login_required
@app.route("/delete-order-item/<int:order_item>")
def delete_order_item(order_item):
  order_item = Order_item.query.get(order_item)
  meal = Meals.query.filter_by(id=order_item.meal).first()
  if order_item:
    db.session.delete(order_item)
    db.session.commit()
    flash(f"{meal.name} has been removed from cart", category="success")
  else:
    flash("Item not found", category="danger")
  return redirect(url_for('cart'))

@login_required
@app.route("/place-order/<int:order>")
def place_order(order):
  order = Order.query.get(order)
  if order:
    order.placed = True
    order.status = "Closed"
    db.session.commit()
    flash(f"Your order #{order.order_id} has been placed. Await confirmation", category="success")
    try:
      em['sender'] = email_sender
      em['to'] = current_user.email
      em['subject'] = f"Order #{order.order_id} has been placed"
      em.set_content(f"Order #{order.order_id} has been placed. Await confirmation of your order")
      context = ssl.create_default_context()
      with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.sendmail(email_sender, current_user.email, em.as_string())
        smtp.quit()
        del em["To"]
    except:
      print("email not sent")
  else:
    flash("Order not found", category="danger")

  return redirect(url_for('orders'))

@login_required
@app.route("/confirm-order/<int:order>")
def confirm_order(order):
  order = Order.query.get(order)
  user = Student.query.filter_by(phone_number=order.user)
  if order:
    order.confirmed = True
    db.session.commit()
    flash(f"Order #{order.order_id} has been confirmed successfully", category="success")
    try:
      em['sender'] = os.environ["Email_from"]
      em['to'] = user.email
      em['subject'] = f"Order {order.order_id} has been confirmed"
      em.set_content(f"Your order #{order.order_id} has been confirmed successfully. You can pick it up in the next 30mins")
      context = ssl.create_default_context()
      with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.sendmail(email_sender, user.email, em.as_string())
        smtp.quit()
        del em["To"]
    except:
      print("email not sent")
  else:
    flash("order not found", category="danger")

  return redirect(url_for('orders'))

@app.route("/delete-order/<int:order>")
@login_required
def delete_order(order):
  order = Order.query.get(order)
  user = Student.query.filter_by(phone_number=order.user)
  if order:
    db.session.delete(order)
    db.session.commit()
    flash(f"Order #{order.order_id} has been declined", category="success")
  else:
    flash("order not found", category="danger")

  return redirect(url_for('orders'))

@login_required
@app.route("/my-orders")
def orders():
  existing_order = Order.query.filter_by(user=current_user.phone_number, status="Active").first()
  orders = Order.query.all()
  meals = Meals.query.all()
  users = []
  students = Student.query.all()
  admins = Admin.query.all()
  for student in students:
    users.append(student)
  for admin in admins:
    users.append(admin)
  order_items = Order_item.query.all()

  return render_template("orders.html", orders=orders, existing_order=existing_order, meals=meals, order_items=order_items, users=users)

@app.route("/add-meal", methods=["POST", "GET"])
def add_meal():
  meals = Meals.query.all()
  meal_names = []
  for meal in meals:
    meal_names.append(meal.name)
  if request.method == "POST":
    if request.form.get("meal-name") in meal_names:
      flash(f"Meal already in the menu", category="warning")
    else:
      new_meal = Meals(
        name=request.form.get("meal-name"),
        price=request.form.get("price"),
        category="meal",
        ref_no=random.randint(100000,999999)
      )
      db.session.add(new_meal)
      db.session.commit()
      flash(f"{new_meal.name} added to the menu", category="success")

  return render_template("new_meal.html")

@app.route("/remove-meal/<int:meal_id>")
def remove_meal(meal_id):
  meal = Meals.query.get(meal_id)
  if meal:
    db.session.delete(meal)
    db.session.commit()
    flash(f"{meal.name} removed from menu", category="info")
  return render_template("meal.html")

@app.route("/logout")
def logout():
  logout_user()
  return redirect(url_for('sign_in'))

if __name__ == '__main__':
  app.run(debug=True)
