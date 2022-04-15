# from logging import log
from flask import render_template, redirect, Flask, session, request, url_for, jsonify
from flask_session import Session
from tempfile import mkdtemp
# import requests
from datetime import datetime
from flask_wtf.csrf import CSRFProtect
from flask_simple_geoip import SimpleGeoIP
from mpu import haversine_distance
from werkzeug.utils import secure_filename
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from authlib.integrations.flask_client import OAuth

from helpers import getConnection, executeWriteQuery, executeReadQuery, login_required

# configure application, use filesystem insted of cookies, make sure responses aren't cached
app = Flask(__name__)
app.secret_key = '5yTuleqqRRdRwvCf'
app.config.update(GEOIPIFY_API_KEY='at_KIgYTxO7GSB26ukH0av9aCEC2IUCQ')
simple_geoip = SimpleGeoIP(app)
csrf = CSRFProtect(app)
app.config["TEMPLATES_AUTO_RELOAD"] = True
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id='400883400079-0mgfa8lv7qco8f9dj1elpg2huv70llcs.apps.googleusercontent.com',
    client_secret='YLdpERED0IZeD80ZPSZ59qIh',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',  # This is only needed if using openId to fetch user info
    client_kwargs={'scope': 'openid email profile'},
)

names = ("Prakamya Singh", "Praneeth Suresh", "Pratyush Bansal", "Rahul Rajkumar")
categories = ("Books", "Stationary", "Clothing", "Household", "Sports", "Electronics", "Toys", "Decorations", "Assorted")
db = getConnection("unic.db")
google = oauth.create_client("google")


# login route
@app.route('/login')
def login():
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)


# authorize google oauth access
@app.route('/authorize')
@csrf.exempt
def authorize():
    token = google.authorize_access_token()
    user_info = google.get('userinfo').json()
    if len(executeReadQuery(db, "SELECT username FROM users WHERE user_id = ?;", (user_info["id"],))) == 0:
        authorize.user_storage_info = (user_info["id"], user_info["email"], f"{user_info['given_name']} {user_info['family_name']}", user_info["picture"])
        return redirect("/user_info")
    session["email"] = user_info["email"]
    session["user_id"] = user_info["id"]
    session["username"] = executeReadQuery(db, "SELECT username FROM users WHERE user_id = ?", (session["user_id"],))[0][0]
    return redirect('/')


# complete user profile(for first-time sign in)
@app.route("/user_info", methods=["GET", "POST"])
def user_info():
    if request.method == "GET":
        userinfo = authorize.user_storage_info
        return render_template("user_info.html", username=userinfo[2], id=userinfo[0], pic=userinfo[3], email=userinfo[1])

    username = request.form.get("username")
    email = request.form.get("email")
    phone_num = request.form.get("phone_num")
    location = request.form.get("location")
    long = request.form.get("long")
    lat = request.form.get("lat")
    pic = request.form.get("pic")
    user_id = request.form.get("user_id")
    query = "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?);"
    vals = (user_id, username, email, pic, phone_num, lat, long, location)
    if executeWriteQuery(db, query, vals):
        session["email"] = email
        session["user_id"] = user_id
        session["username"] = username
        return redirect("/")


# user can check account information
@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    if request.method == "GET":
        query = "SELECT picture, phone_num, location FROM users WHERE user_id = ?"
        xtra_info = executeReadQuery(db, query, (session["user_id"],))[0]
        account_info = (session["email"], session["username"], xtra_info[0], xtra_info[1], xtra_info[2])
        query = "SELECT * FROM mentors WHERE mentor = ?"
        mentorships = executeReadQuery(db, query, (session["user_id"],))
        query = "SELECT * FROM listings WHERE seller = ? AND availability = 1"
        listings_uploaded = executeReadQuery(db, query, (session["user_id"],))
        return render_template("account.html", info=account_info, mentorships=mentorships, listings=listings_uploaded)
    
    username = request.form.get("username")
    phone_num = request.form.get("phone_num")
    location = request.form.get("location")
    lat = request.form.get("lat")
    long = request.form.get("long")
    session["username"] = username
    query = "UPDATE users SET username = ?, phone_num = ?, location = ?, latitude = ?, longitude = ? WHERE user_id = ?"
    vals = (username, phone_num, location, lat, long, session["user_id"])
    if executeWriteQuery(db, query, vals):
        return redirect("/account")


# home page
@app.route("/")
def homepage():
    if session.get("user_id", None):
        return render_template("home.html", logged_in=True)
    return render_template("home.html", logged_in=False)


# logout the user
@app.route('/logout')
@login_required
def logout():
    session.clear()
    return redirect('/')


# user can sell items
@app.route('/uni_shop/sell', methods=["GET", "POST"])
@login_required
def sell():
    if request.method == "GET":
        # render the form to sell an item
        return render_template("sell.html", categories=categories)

    # get the item details
    category = request.form.get("category")
    usage = request.form.get("usage")
    item_name = request.form.get("item_name")
    proddesc = request.form.get("item_descr")
    timestamp = datetime.now().strftime("%B %d, %Y %H:%M:%S")
    query = "INSERT INTO listings (seller, item_name, description, category, usage, availability, timestamp) VALUES (?, ?, ?, ?, ?, 1, ?);"
    values = (session["user_id"], item_name, proddesc, category, usage, timestamp,)
    # insert the new item into db
    if executeWriteQuery(db, query, values):
        return render_template("sell.html", sold=True)


# show all available items
@app.route("/uni_shop")
@login_required
def uni_shop():
    query = "SELECT * FROM listings WHERE availability = 1 ORDER BY listing_id DESC;"
    listings_data = executeReadQuery(db, query)
    listings = []
    for l in listings_data:
        uploader = executeReadQuery(db, "SELECT username FROM users WHERE user_id = ?", (l[1],))[0]
        l += uploader
        listings.append(l)
    return render_template("shop.html", listings=listings)


# show details on particular item
@app.route("/uni_shop/item/<int:listing_id>")
@login_required
def see_item(listing_id):
    query = "SELECT * FROM listings WHERE listing_id = ?"
    listing = executeReadQuery(db, query, (listing_id,))[0]
    query = "SELECT username, phone_num, latitude, longitude, location FROM users WHERE user_id = ?"
    seller = executeReadQuery(db, query, (listing[1],))[0]
    user = executeReadQuery(db, "SELECT latitude, longitude FROM users WHERE user_id = ?", (session["user_id"],))[0]
    dist = haversine_distance((seller[2], seller[3],), (user[0], user[1],))
    if dist >= 1:
        display_dist = f"{dist:.1f} km"
    else:
        display_dist = f"{dist:.1f} meters"
    return render_template("see_item.html", listing=listing, seller=seller, dist=dist, display_dist=display_dist)


@app.route("/uni_shop/item/mark_sold/<int:listing_id>")
@login_required
def mark_as_sold(listing_id):
    query = "SELECT seller FROM listings WHERE listing_id = ?"
    seller = executeReadQuery(db, query, (listing_id,))[0][0]
    if seller != session["user_id"]:
        return render_template("nope.html")
    
    query = "UPDATE listings SET availability = 0 WHERE listing_id = ?"
    if executeWriteQuery(db, query, (listing_id,)):
        return redirect("/account")



# filter items in store by category and usage
@app.route("/uni_shop/filter", methods=["GET", "POST"])
@login_required
def choices():
    if request.method == "GET":
        # render form to filter out items in shop
        return render_template('shop_filter.html', categories=categories)

    # get the user's choices and make them available to other functions
    choices.category = request.form.get("category")
    choices.usage = request.form.get("usage")
    return redirect("/uni_shop/filter/results")


# show filtered items
@app.route("/uni_shop/filter/results")
@login_required
def findlistings():
    # filter items from db using user's choice
    query = "SELECT * FROM listings WHERE availability = 1 AND category = ? AND usage = ? ORDER BY listing_id DESC;"
    listings_data = executeReadQuery(db, query, (choices.category, choices.usage,))
    listings = []
    for l in listings_data:
        uploader = executeReadQuery(db, "SELECT username FROM users WHERE user_id = ?", (l[1],))[0]
        l += uploader
        listings.append(l)
    return render_template("shop.html", listings=listings)


# redirect to chat with mentor
@app.route("/uni_shop/item/chat/redirect", methods=["GET", "POST"])
@login_required
def processing():
    if request.method == "GET":
        return redirect("/uni_shop")
        
    phone_num = request.form.get("phone_num")
    x = phone_num.split()
    phone_num = "".join(x)
    return redirect(f"https://wa.me/{phone_num}")


# sign up as a mentor
@app.route('/mentor/signup', methods=["GET", "POST"])
@login_required
def signmentor():
    if request.method == "GET":
        # render form to sign up as mentor
        return render_template("sign_mentor.html")

    # get the user's area chosen and self-description
    area = request.form.get("expertin")
    descr = request.form.get("descr")
    query = "INSERT INTO mentors (mentor, description, area) VALUES (?, ?, ?);"
    values = (session["user_id"], descr, area,)
    # add user into db
    if executeWriteQuery(db, query, values):
        return render_template("sign_mentor.html", registered=True)


# resign a mentorship
@app.route("/mentor/resign/<int:mentor_id>")
@login_required
def resign(mentor_id):
    query = "SELECT mentor FROM mentors WHERE mentor_id = ?"
    mentor = executeReadQuery(db, query, (mentor_id,))[0][0]
    if mentor != session["user_id"]:
        return render_template("nope.html")
    
    query = "DELETE FROM mentors WHERE mentor_id = ?"
    if executeWriteQuery(db, query, (mentor_id,)):
        return redirect("/account")


# search for a mentor based on area of expertise
@app.route("/mentor/search", methods=["GET", "POST"])
@login_required
def mentorpreferences():
    if request.method == "GET":
        return render_template('mentor_search.html')

    mentorpreferences.area = request.form.get("expertin")
    return redirect("/mentor/search/results")


# filter out mentors based on chosen area of expertise
@app.route("/mentor/search/results")
@login_required
def mentorlistings():
    query = "SELECT * FROM mentors WHERE area = ? ORDER BY mentor_id DESC;"
    area = mentorpreferences.area
    mentors_data = executeReadQuery(db, query, (area,))
    mentors = []
    for m in mentors_data:
        uploader = executeReadQuery(db, "SELECT username FROM users WHERE user_id = ?", (m[1],))[0]
        m += uploader
        mentors.append(m)
    return render_template('mentor_results.html', mentors=mentors, area=area)


# see mentor details
@app.route("/mentor/mentor_id/<int:mentor_id>")
@login_required
def show_mentor(mentor_id):
    query = "SELECT * FROM mentors WHERE mentor_id = ?"
    mentor = executeReadQuery(db, query, (mentor_id,))[0]
    query = "SELECT username, phone_num, latitude, longitude, location FROM users WHERE user_id = ?"
    guy = executeReadQuery(db, query, (mentor[1],))[0]
    user = executeReadQuery(db, "SELECT latitude, longitude FROM users WHERE user_id = ?", (session["user_id"],))[0]
    dist = haversine_distance((guy[2], guy[3],), (user[0], user[1],))
    if dist >= 1:
        display_dist = f"{dist:.1f} km"
    else:
        display_dist = f"{dist:.1f} meters"
    return render_template("see_mentor.html", mentor=mentor, guy=guy, dist=dist, display_dist=display_dist)


# redirect to chat with mentor
@app.route("/mentor/mentor_id/chat/redirect", methods=["GET", "POST"])
@login_required
def processing1():
    if request.method == "GET":
        return redirect("/mentor/search")
    
    phone_num = request.form.get("phone_num")
    x = phone_num.split()
    phone_num = "".join(x)
    return redirect(f"https://wa.me/{phone_num}")


# error handling
def errorhandler(e):
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return render_template("error.html", name=e.name, code=e.code, description=e.description)

# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

# show info about website(pretty useless but we'll keep it)
@app.route("/about")
@login_required
def about():
    return render_template('about.html', names=names)

if __name__ == "__main__":
    app.run()