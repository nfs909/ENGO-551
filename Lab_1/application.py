from importlib.resources import Resource
import os
from pickle import NONE

from flask import Flask, jsonify, redirect, request, session
from flask_session import Session
from flask import render_template
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import requests
import re


app = Flask(__name__)
app.secret_key = os.urandom(24)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def home():
    return render_template('login.html')

@app.route("/signup")
def login():
    return render_template('signup.html')


@app.route("/validation", methods = ['POST'])
def valid():
    
    user_name = request.form.get('nm')
    password = request.form.get('ps')
    user = db.execute("SELECT * FROM auth WHERE username = '{}' and password = '{}'".format(user_name, password)).fetchall()

    num = 0
    for i in user:
        num+=1
    
    if num > 0:
        session['user_id'] = user[0].username
        return redirect('/search')
    else:
        return render_template('loginfail.html')


@app.route("/logout")
def logout():
    session.pop('user_id')
    return render_template('login.html')


@app.route("/add_user", methods = ['POST'])
def add_user():
    empty = ''
    user_name = request.form.get('nm')
    password = request.form.get('ps')

    user = db.execute("SELECT * FROM auth WHERE username = '{}'".format(user_name)).fetchall()

    num = 0
    for i in user:
        num+=1

    if user_name != empty and password != empty and num == 0:
        db.execute("INSERT INTO auth (username, password) Values ('{}', '{}')".format(user_name, password))
        db.commit()
    
    if user_name == empty or password == empty:
        return render_template('signupnone.html')
    elif num > 0:
        return render_template('signuptakenuser.html')
    else:
        return render_template('login.html')


@app.route("/search")
def search():
    if 'user_id' in session:
        return render_template('search.html')
    else:
        return render_template('login.html')



@app.route("/find", methods = ['POST'])
def find():
    book= request.form.get('nm')
    isbn = request.form.get('ps')
    author = request.form.get('auth')
    book = db.execute("SELECT * FROM books WHERE title LIKE '%{}%' and isbn LIKE '%{}%' and author LIKE '%{}%'".format(book.capitalize(), isbn, author.capitalize())).fetchall()

    headings = ("Book", "Author", "ISBN")

    num = 0
    for i in book:
        num+=1
    
    if num > 0:
        return render_template('list.html', headings = headings, book = book)
    else:
        return render_template('searchfailed.html')


@app.route("/find/<string:book_isbn>")
def specbook(book_isbn):
    book = db.execute("SELECT * FROM books WHERE isbn = '{}'".format(str(book_isbn))).fetchall()
    review = db.execute("SELECT * FROM reviews WHERE isbn = '{}'".format(str(book_isbn))).fetchall()
    user = session['user_id']
    api_key = 'AIzaSyCYeG_jysQkoGrS7Dld_qBvg92ge-gyss4'
    rp = requests.get("https://www.googleapis.com/books/v1/volumes?q={}&key={}".format(book_isbn,api_key))
    r = rp.json()
    rank = 0
    for i in r['items']:
        isbn_val=str(i['volumeInfo']['industryIdentifiers'])
        ap = re.search(r"\b{}\b".format(str(book_isbn)), isbn_val, re.IGNORECASE)
        if ap is not None:
            break
        rank+=1

    rating = r["items"][rank]['volumeInfo']['averageRating']

    if rating is None:
        rating = 'N/A'
    
    num_review = 0

    for i in review:
        if i.username == str(user):
            num_review +=1
    if num_review == 0:
        return render_template('book.html', book = book, review=review, rating = rating)
    else:
        return render_template('book_noreview.html', book = book, review=review, rating = rating)

        
@app.route("/submit/<string:isbn>")
def submit(isbn):
    book = db.execute("SELECT * FROM books WHERE isbn = '{}'".format(str(isbn))).fetchall()

    return render_template('review.html', book = book)


@app.route("/newreview/<string:isbn>", methods = ['POST'])
def newreview(isbn):
    user = session['user_id']
    rating= request.form.get('rn')
    review = request.form.get('rv')
    db.execute("INSERT INTO reviews (username, isbn, review, rating) Values ('{}', '{}', '{}', '{}')".format(str(user), str(isbn), str(review), int(rating)))
    db.commit()
    return render_template('submit.html')


@app.route("/api/<string:isbn>")
def api(isbn):
    api_key = 'AIzaSyCYeG_jysQkoGrS7Dld_qBvg92ge-gyss4'
    rp = requests.get("https://www.googleapis.com/books/v1/volumes?q={}&key={}".format(isbn,api_key))
    r = rp.json()
    rank = 0
    for i in r['items']:
        isbn_val=str(i['volumeInfo']['industryIdentifiers'])
        ap = re.search(r"\b{}\b".format(isbn), isbn_val, re.IGNORECASE)
        if ap is not None:
            break
        rank+=1

    rating = r["items"][rank]['volumeInfo']['averageRating']
    title = r['items'][rank]['volumeInfo']['title']
    author = r['items'][rank]['volumeInfo']['authors'][0]
    pub_d = r['items'][rank]['volumeInfo']['publishedDate']
    review_c = r['items'][rank]['volumeInfo']['ratingsCount']
    isbn13 = 'N/A'
    isbn10 = 'N/A'
    for i in range(len(r['items'][rank]['volumeInfo']['industryIdentifiers'])):
        if r['items'][rank]['volumeInfo']['industryIdentifiers'][i]['type'] == str('ISBN_13'):
            isbn13 = r['items'][rank]['volumeInfo']['industryIdentifiers'][i]['identifier']
        if r['items'][rank]['volumeInfo']['industryIdentifiers'][i]['type'] == str('ISBN_10'):
            isbn10 = r['items'][rank]['volumeInfo']['industryIdentifiers'][i]['identifier']



    return jsonify({
                    "Title" : title,
                    "Author": author,
                    "Published Date": pub_d,
                    "Average Rating": rating,
                    "Number of Reviews": review_c,
                    "ISBN_13" : isbn13,
                    "ISBN_10" : isbn10
    })


