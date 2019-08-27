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
    rows = db.execute("SELECT officials.name, officials.term_start, officials.position_id, positions.title, positions.link, positions.term_length, positions.term_limit, positions.description,  parties.party, scales.scale, areas.area FROM officials LEFT JOIN positions ON officials.position_id = positions.id LEFT JOIN parties ON officials.party_id = parties.id LEFT JOIN areas ON positions.area_id = areas.id LEFT JOIN scales ON positions.scale_id = scales.id ORDER BY scale_id, officials.position_id, officials.name")
    for row in rows:
        if not row["term_limit"]:
            row["term_limit"] = "None"
        if not row["term_length"]:
            row["term_length"] = "Lifetime"
        check = db.execute("SELECT * FROM officials WHERE position_id = :position_id ORDER BY name", position_id=row["position_id"])
        if check[0]["name"] == row["name"]:
            row["count"] = len(check)
        else:
            row["count"] = 0
        
        
    scales = {}
    for row in rows:
        if not row["scale"] in scales:
            scales[row["scale"]] = {}
            
        if not row["area"] in scales[row["scale"]]:
            scales[row["scale"]][row["area"]] = []
        
        scales[row["scale"]][row["area"]].append({"name" : row["name"], "title" : row["title"], "description" : row["description"], "title" : row["title"], "term_limit" : row["term_limit"], "term_length" : row["term_length"], "party" : row["party"], "term_start" : row["term_start"], "link" : row["link"], "count" : row["count"]})
    
    print(scales)
    
    return render_template("index.html", scales=scales)

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
        edit = request.form.get("position_edit")
        position = request.form.get("position")
        fields = { "title" : request.form.get("position_title"),
                   "scale_id" : request.form.get("position_scale"),
                   "area_id" : request.form.get("position_area"),
                   "link" : request.form.get("position_link"),
                   "term_length" : request.form.get("position_length"),
                   "term_limit" : request.form.get("position_limit"),
                   "description" : request.form.get("position_description")}
        
        if edit == "add":
            
            for key, field in fields.items():
                if not field:
                    return apology("Empty " + key)
             
            rows = db.execute("INSERT INTO positions (title, scale_id, area_id, link, term_length, term_limit, description) VALUES (:title, :scale_id, :area_id, :link, :term_length, :term_limit, :description)", 
                               title=fields["title"], scale_id=fields["scale_id"], area_id=fields["area_id"], link=fields["link"], term_length=fields["term_length"], term_limit=fields["term_limit"], description=fields["description"])
            if not rows:
                return apology("Error inserting")
                
        elif edit == "delete":
            if not position or position == "default" or position == "new":
                return apology("Empty Position")
            
            rows = db.execute("SELECT * FROM positions WHERE id = :id", id=position)
    
            if not len(rows):
                return apology("That Position doesn't exist!")
            
            db.execute("DELETE FROM positions WHERE id = :id", id=position)
                
        elif edit == "edit":
            if not position or position == "default" or position == "new":
                return apology("Empty Position")
        
            rows = db.execute("SELECT * FROM positions WHERE id = :id", id=position)
    
            if not len(rows):
                return apology("That Position doesn't exist!")
            
            for key, field in fields.items():
                if ((key == "scale_id" or key == "area_id") and ("Select" in field)):
                    continue
                if field:
                    db.execute("UPDATE positions SET :key = :field WHERE id = :id", key=key, id=position, field=field)
                
        else:
            return apology("Edit Type Error")
            
        return changes()
    else:
        return changes()

@app.route("/edit_official", methods=["GET", "POST"])
@login_required
def change_official():
    if request.method == "POST":
        edit = request.form.get("official_edit")
        official = request.form.get("official")
        fields = { "name" : request.form.get("official_name"),
                   "position_id" : request.form.get("official_position"),
                   "party_id" : request.form.get("official_party"),
                   "term_start" : request.form.get("official_start")}
        print(official)
        if edit == "add":
            
            for key, field in fields.items():
                if not field:
                    return apology("Empty " + key)
             
            rows = db.execute("INSERT INTO officials (name, position_id, party_id, term_start) VALUES (:name, :position_id, :party_id, :term_start)", 
                               name=fields["name"], position_id=fields["position_id"], party_id=fields["party_id"], term_start=fields["term_start"])
            if not rows:
                return apology("Error inserting")
                
        elif edit == "delete":
            if not official or official == "default" or official == "new":
                return apology("Empty Official")
            
            rows = db.execute("SELECT * FROM officials WHERE name = :name", name=official)
    
            if not len(rows):
                return apology("That official doesn't exist!")
            
            db.execute("DELETE FROM officials WHERE name = :name", name=official)
                
        elif edit == "edit":
            if not official or official == "default" or official == "new":
                return apology("Empty Official")
        
            rows = db.execute("SELECT * FROM officials WHERE name = :name", name=official)
    
            if not len(rows):
                return apology("That official doesn't exist!")
            
            for key, field in fields.items():
                if ((key == "party_id" or key == "position_id") and ("Select" in field)):
                    continue
                if field:
                    db.execute("UPDATE officials SET :key = :field WHERE name = :name", key=key, name=official, field=field)
                
        else:
            return apology("Edit Type Error")
            
        return changes()
    else:
        return changes()

@app.route("/changes", methods=["GET"])
@login_required
def changes():
    officials = db.execute("SELECT officials.*, positions.title, parties.party FROM officials LEFT JOIN positions ON officials.position_id = positions.id LEFT JOIN parties ON officials.party_id = parties.id")
    
    positions = db.execute("SELECT positions.*, scales.scale, areas.area FROM positions LEFT JOIN scales ON positions.scale_id = scales.id LEFT JOIN areas ON positions.area_id = areas.id")
    for p in positions:
        if not p["term_limit"]:
            p["term_limit"] = "None"
        if not p["term_length"]:
            p["term_length"] = "Lifetime"
            
    
    scales = db.execute("SELECT * FROM scales")
    parties = db.execute("SELECT * FROM parties")
    areas = db.execute("SELECT * FROM areas")
    return render_template("changes.html", parties=parties, areas=areas, scales=scales, positions=positions, officials=officials)