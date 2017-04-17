from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import gettempdir

from helpers import *

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# custom filter
app.jinja_env.filters["usd"] = usd

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = gettempdir()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

@app.route("/")
@login_required
def index():
    
    stocks = db.execute("SELECT * FROM history WHERE user_id = :id GROUP BY symbol", id=session["user_id"])
    cash = db.execute("SELECT cash from users WHERE id = :id", id=session["user_id"])
    total = cash[0]["cash"]

    for i, stock in enumerate(stocks):
        quote = lookup(stock["symbol"])
        stock["name"] = quote["name"]
        stock["price"] = quote["price"]
        stock["shares"] = db.execute("SELECT SUM(shares) FROM history WHERE user_id = :id AND symbol = :symbol", id=session["user_id"], symbol=stock["symbol"])[0]["SUM(shares)"]
        stock["total"] =  stock["shares"] * quote["price"]
        total += stock["total"]
        stock["total"] = usd(stock["total"])
        
    for i, stock in enumerate(stocks):
        if stock["shares"] == 0:
            del(stocks[i])
            
        
    print(stocks)
    return render_template("index.html", stocks=stocks, total=usd(total), cash=usd(cash[0]["cash"]))

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("Missing symbol!")
        elif not request.form.get("shares"):
            return apology("Missing shares!")
        
        quote = lookup(request.form.get("symbol"))
        
        shares = int(request.form.get("shares"))
        
        if not quote:
            return apology("Invalid symbol")
        if not shares > 0:
            return apology("Invalid shares")
        
        cash = db.execute("SELECT cash FROM users WHERE id = :id", id=session["user_id"])
        
        if cash[0]["cash"] < quote["price"] * shares:
            return apology("Not enough money")
        
        db.execute("UPDATE users SET cash = cash - :price WHERE id = :id", price=quote["price"] * shares, id=session["user_id"])
        
        db.execute("INSERT INTO history (user_id, symbol, shares, price) VALUES (:user_id, :symbol, :shares, :price)", user_id=session["user_id"], symbol=quote["symbol"], shares=shares, price=quote["price"])
        
        return redirect(url_for("index"))
    else:
        return render_template("buy.html")

@app.route("/history")
@login_required
def history():
    """Show history of transactions."""
    stocks = db.execute("SELECT * FROM history WHERE user_id = :id", id=session["user_id"])

    print(stocks)
    return render_template("history.html", stocks=stocks)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            return apology("invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))

@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    
    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("Missing symbol!")
        
        quote = lookup(request.form.get("symbol"))
        
        if not quote:
            return apology("Invalid Symbol")
            
        return render_template("quoted.html", name=quote["name"], symbol=quote["symbol"], price=quote["price"])
    else:
        return render_template("quote.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("Missing username!")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("Missing password!")
            
        elif not request.form.get("confirmation"):
            return apology("Missing confirmation!")
        
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("password and conformation password didn't match")
            
            
        hash = pwd_context.encrypt(request.form.get("password"))    
        
        result = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", username=request.form.get("username"), hash=hash)
        
        if not result:
            return apology("Username taken")
        
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))
        
        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect(url_for("index"))
        
    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("Missing symbol!")
        elif not request.form.get("shares"):
            return apology("Missing shares!")
        
        quote = lookup(request.form.get("symbol"))
        
        shares = -int(request.form.get("shares"))
        
        if not quote:
            return apology("Invalid symbol")
        if not shares < 0:
            return apology("Invalid shares")
        
        stock = db.execute("SELECT SUM(shares) FROM history WHERE user_id = :id AND symbol = :symbol", id=session["user_id"], symbol=quote["symbol"])[0]["SUM(shares)"]
        
        if not stock:
            return apology("You don't own this stock!")
        
        if shares + stock < 0:
            return apology("You don't have that many shares!")
        
        db.execute("UPDATE users SET cash = cash - :price WHERE id = :id", price=quote["price"] * shares, id=session["user_id"])
        
        db.execute("INSERT INTO history (user_id, symbol, shares, price) VALUES (:user_id, :symbol, :shares, :price)", user_id=session["user_id"], symbol=quote["symbol"], shares=shares, price=quote["price"])
        
        return redirect(url_for("index"))
    else:
        return render_template("sell.html")


@app.route("/cash", methods=["GET", "POST"])
@login_required
def cash():
    """Get stock quote."""
    
    if request.method == "POST":
        if not request.form.get("cash"):
            return apology("Missing amount!")
        
        cash = int(request.form.get("cash"))
        
        if cash > 1000000 or cash < 0:
            return apology("Cash must be a positive integer less than 1 million")
            
        db.execute("UPDATE users SET cash = cash + :add WHERE id = :id", add=cash, id=session["user_id"])    
        
        return redirect(url_for("index"))
    else:
        return render_template("cash.html")
