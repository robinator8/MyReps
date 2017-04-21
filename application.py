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

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = gettempdir()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///reps.db")

@app.route("/home")
@app.route("/index")
@app.route("/")
def index():   
   return render_template("index.html")

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
        
        username = request.form.get("username").lower()
        
        rows = db.execute("SELECT * FROM users WHERE lower(username) = :username", username=username)

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
        
        username = request.form.get("username")
        
        rows = db.execute("SELECT * FROM users WHERE lower(username) = :username", username=username.lower())
        if rows:
            return apology("Username taken")
        
        rows = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", username=username, hash=hash)
        
        if not rows:
            return apology("Username taken")
        
        rows = db.execute("SELECT * FROM users WHERE lower(username) = :username", username=username.lower())
        
        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect(url_for("index"))
        
    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/add_party", methods=["GET", "POST"])
@login_required
def add_party():
    if request.method == "POST":
        if not request.form.get("add_party"):
            return apology("Empty Party")
        
        rows = db.execute("SELECT party FROM parties WHERE party = :party", party=request.form.get("add_party"))

        if len(rows):
            return apology("That Party is already added!")
        
        db.execute("INSERT INTO parties (party) VALUES (:party)", party=request.form.get("add_party"))
        return changes()

    else:
        return changes()

@app.route("/del_party", methods=["GET", "POST"])
@login_required
def del_party():
    if request.method == "POST":
        if not request.form.get("del_party"):
            return apology("Empty Party")
        
        rows = db.execute("SELECT party FROM parties WHERE party = :party", party=request.form.get("del_party"))

        if not len(rows):
            return apology("That Party doesn't exist!")
        
        db.execute("DELETE FROM parties WHERE party = :party", party=request.form.get("del_party"))
        return changes()

    else:
        return changes()

@app.route("/add_area", methods=["GET", "POST"])
@login_required
def add_area():
    if request.method == "POST":
        if not request.form.get("add_area"):
            return apology("Empty Area")
        
        rows = db.execute("SELECT area FROM areas WHERE area = :area", area=request.form.get("add_area"))

        if len(rows):
            return apology("That Party is already added!")
        
        db.execute("INSERT INTO areas (area) VALUES (:area)", area=request.form.get("add_area"))
        return changes()

    else:
        return changes()

@app.route("/del_area", methods=["GET", "POST"])
@login_required
def del_area():
    if request.method == "POST":
        if not request.form.get("del_area"):
            return apology("Empty Area")
        
        rows = db.execute("SELECT area FROM areas WHERE area = :area", area=request.form.get("del_area"))

        if not len(rows):
            return apology("That Area doesn't exist!")
        
        db.execute("DELETE FROM areas WHERE area = :area", area=request.form.get("del_area"))
        return changes()

    else:
        return changes()

@app.route("/add_scale", methods=["GET", "POST"])
@login_required
def add_scale():
    if request.method == "POST":
        
        if not request.form.get("add_scale"):
            return apology("Empty Scale")
        
        rows = db.execute("SELECT scale FROM scales WHERE scale = :scale", scale=request.form.get("add_scale"))

        if len(rows):
            return apology("That Party is already added!")
        
        db.execute("INSERT INTO scales (scale) VALUES (:scale)", scale=request.form.get("add_scale"))
        return changes()

    else:
        return changes()

@app.route("/del_scale", methods=["GET", "POST"])
@login_required
def del_scale():
    if request.method == "POST":
        if not request.form.get("del_scale"):
            return apology("Empty Scale")
        
        rows = db.execute("SELECT scale FROM scales WHERE scale = :scale", scale=request.form.get("del_scale"))

        if not len(rows):
            return apology("That Scale doesn't exist!")
        
        db.execute("DELETE FROM scales WHERE scale = :scale", scale=request.form.get("del_scale"))
        return changes()

    else:
        return changes()

@app.route("/edit_position", methods=["GET", "POST"])
@login_required
def change_position():
    if request.method == "POST":
        print(request.form.get("position_edit"))
        if request.form.get("position_edit") == "add":
            db.execute("INSERT INTO positions (title, scale_id, area_id, link, term_length, term_limit, description) VALUES (:title, :scale_id, :area_id, :link, :term_length, :term_limit, :description)", title=title, scale_id=scale_id, area_id=area_id, link=link, term_length=term_length, term_limit=term_limit, description=description)
        elif request.form.get("position_edit") == "delete":
            print("Delete")
        elif request.form.get("position_edit") == "edit":
            print("Edit")
        else:
            return apology("Edit Type Error")
        return changes()
    else:
        return changes()

@app.route("/changes", methods=["GET"])
@login_required
def changes():
    positions = db.execute("SELECT title, link, term_length, term_limit, description, scales.scale, areas.area FROM positions LEFT JOIN scales ON positions.scale_id = scales.id LEFT JOIN areas ON positions.area_id = areas.id")
    
    for p in positions:
        if not p["term_limit"]:
            p["term_limit"] = "None"
        if not p["term_length"]:
            p["term_length"] = "Lifetime"
            
    
    scales = db.execute("SELECT * FROM scales")
    parties = db.execute("SELECT * FROM parties")
    areas = db.execute("SELECT * FROM areas")
    return render_template("changes.html", parties=parties, areas=areas, scales=scales, positions=positions)