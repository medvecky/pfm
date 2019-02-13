import os
import datetime
from flask import Flask, session, request, jsonify, redirect
from flask_session import Session
from tempfile import mkdtemp
from flask import render_template
from helpers import apology, login_required
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
from models import *

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
#app.config["SESSION_FILE_DIR"] = mkdtemp()
# app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "memcached"
# Set the secret key to some random bytes. Keep this really secret!
# Session(app)


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """
    Application main page
    """
    # get current user
    user = User.query.filter_by(id=session["user_id"]).first()
    print("Current user id={} email={}".format(user.id, user.email))

    # get date period
    begindate = datetime.datetime.today()
    begindate = begindate.replace(day=1)
    begin = begindate.strftime('%Y-%m-%d')

    try:
        nextmonthdate = begindate.replace(month=begindate.month + 1)
    except ValueError:
        if begindate.month == 12:
            nextmonthdate = begindate.replace(year=begindate.year + 1, month=1)


    end = nextmonthdate.strftime('%Y-%m-%d')

    print(begin)
    print(end)

    # generates expenditures category, sum tuple
    expendituresData = []
    expendituresSum = 0
    categories = Category.query.all()
    overalSum = 0
    for category in categories:
        categorySum = 0
        expenditures = Expenditure \
        .query \
        .filter_by(user_id=user.id) \
        .filter_by(categories_id=category.id) \
        .filter(Expenditure.date >= begin) \
        .filter(Expenditure.date < end) \
        .all()
        for expenditure in expenditures:
            categorySum += expenditure.price
        expendituresData.append((category.name,categorySum))
        # accumulates overal sum from all categories
        expendituresSum += categorySum

    #get income data for period
    incomes = Income \
    .query\
    .filter_by(user_id=user.id)\
    .filter(Income.date >= begin)\
    .filter(Income.date < end) \
    .all()

    incomesTotal = 0
    for income in incomes:
        incomesTotal += income.value


    return render_template(
        "index.html",
        expendituresData=expendituresData,
        expendituresSum=expendituresSum,
        incomes=incomes,
        incomesTotal=incomesTotal)


@app.route("/inputmain")
@login_required
def inputmain():
    return render_template("expinputmain.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
     # Forget any user_id
    session.clear()

     # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("email"):
            return apology("must provide email", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        user = User.query.filter_by(email=request.form.get("email")).first()

        # Ensure username exists and password is correct
        if not user.id or not check_password_hash(str(user.hashstring), request.form.get("password")):
            return apology("invalid email and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = user.id

        # Redirect user to home page
        return redirect("/")
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


# @app.route('/signup', methods=["GET", "POST"])
# def signup():
#     """
#     Register user
#     :return:
#     """
#     # param validation
#     if request.method == "POST":
#         if not request.form.get("email"):
#             return apology("must provide email", 400)
#         elif not request.form.get("password"):
#             return apology("must provide password", 400)
#         elif not request.form.get("confirmation"):
#             return apology("must provide confirmation", 400)
#         elif request.form.get("confirmation") != request.form.get("password"):
#             return apology("password and confirmation must match", 400)
#         else:
#             # generate hash for entered password
#             passwordHash = generate_password_hash(request.form.get("password"))


#             # check for user exists already

#             if User.query.filter_by(email=request.form.get("email")).count() > 0:
#                 return apology("User already exist", 403)

#             # add user to db
#             User.add_user(
#                 User,
#                 email=request.form.get("email"),
#                 hashstring=passwordHash)
#             # request base for id
#             id = User.query.filter_by(email=request.form.get("email")) \
#                 .first() \
#                 .id
#             # add id to session
#             session["user_id"] = id
#             return redirect("/")
#     else:
#         return render_template("signup.html")

@app.route('/check_user', methods=["GET"])
def check_user():
    """
    Check user existence by email
    :return:
    True or False
    """
    email = request.args.get("email")
    user = User.query.filter_by(email=email).first()
    if user:
        return jsonify(True)
    else:
        return jsonify(False)


@app.route('/check_credentials', methods=["GET"])
def check_credentials():
    """
    Check user credentials
    :return:
    True or False
    """
    email = request.args.get("email")
    password = request.args.get("password")
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify(False)
    hashstring = str(user.hashstring)
    if check_password_hash(user.hashstring, password):
        return jsonify(True)
    else:
        return jsonify(False)


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


if __name__ == '__main__':
    app.run()
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
