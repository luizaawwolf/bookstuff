from flask import Flask, render_template, request
import requests
import urllib.request
from bs4 import BeautifulSoup
from betterreads import client
import urllib.parse
import math
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy.schema import PrimaryKeyConstraint


app = Flask(__name__)
SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    username="annaluizabr",
    password="pythonanywhere",
    hostname="annaluizabr.mysql.pythonanywhere-services.com",
    databasename="annaluizabr$goodoutlet",
)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

app = Flask(__name__)

class Subscription(db.Model):
    __tablename__ = "subscription"
    __table_args__ = (
        PrimaryKeyConstraint('book_id', 'subscriber_id'),
    )
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    subscriber_id = db.Column(db.Integer, db.ForeignKey('subscriber.goodreads_id'))

class Book(db.Model):
    __tablename__ = "book"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(4096),primary_key=False)
    author = db.Column(db.String(4096),primary_key=False)
    subscribers = relationship('Subscriber', secondary = 'subscription')

class Subscriber(db.Model):
	__tablename__ = "subscriber"
	goodreads_id = db.Column(db.Integer,primary_key=True)
	email = db.Column(db.String(4096),primary_key=False)
	current_books = relationship('Book', secondary = 'subscription')
	alert_on_new = db.Column(db.Boolean,primary_key=False)
	alert_on_loss = db.Column(db.Boolean,primary_key=False)

@app.route("/", methods=['GET','POST'])
def home_view():
	if request.method == "GET":
		return render_template("main_page.html")
	api_key = "Eny1ro9b7mxhs8CuFj2o6w"
	api_secret = "bQKcvwYsv0ceEBjk95guDtguTXRUSgBxGPBT0YtxD6U"
	gc = client.GoodreadsClient(api_key, api_secret)
	user_id = int( request.form['user_id'] )
	user = gc.user(user_id)
	if 'private' in list(user.__dict__['_user_dict'].keys()) and user.__dict__['_user_dict']['private'] == 'true':
		return render_template("main_page.html",successes="Oops! Looks like your profile is on private. You can change this in Goodreads -> Account Settings -> Settings -> Privacy")
	gr_books = user.per_shelf_reviews(shelf_name = "to-read")
	valid_books = []
	error=False
	successful_processes = 0
	shelf_size = 0
	for book in gr_books:
		temp_book = book.book
		title = temp_book["title"]
		author = temp_book["authors"]["author"]["name"]
		results = bookOutletHas(title=title, author=author)
		if results:
			print(results)
			if results[0] == "ERROR":
			    error=True
			    continue
			else:
			    successful_processes += 1

		if results:
			for result in results:
				valid_books += [result]
		shelf_size += 1

	successes = "Out of the " + str(shelf_size) + " books processed from your Goodreads to-read shelf, " + str( successful_processes ) + " are on Book Outlet"
	numrows = math.ceil( len(valid_books)/4 )
	return render_template("main_page.html",books=valid_books,err=error,successes=successes )

def bookOutletHas(title, author):
	title = title.split(" (")[0]
	title_url = urllib.parse.quote_plus(title)
	url = 'https://bookoutlet.com/Store/Search?qf=All&q=' + title_url
	response = requests.get(url)
	soup = BeautifulSoup(response.text, 'html.parser')
	items = soup.findAll('div','grid-item')
	search_results = []
	if items and ( len(items[0]) < 2 ):
		search_results += ["ERROR"]
		return search_results
	correct_title = False;
	correct_author = True; #True
	for a in items:
	    ret_author = a.find('p','author').find_all(text=True)[0]
	    ret_author = ret_author.replace(",","")
	    ret_title = a.find('a','line-clamp-2').find_all(text=True)[0]
	    ret_title = ret_title.split("(")[0].strip()
	    title = title.split("(")[0].strip()
	    if title.lower() == ret_title.lower():
	        print(ret_title.lower() + " by " + ret_author)
	        correct_title = True
	    else:
	        continue
	    for name in author.lower().split():
	        if name not in ret_author.lower().split():
	            correct_author = False
	            continue
	    if( correct_title and correct_author):
	        link_url = "https://bookoutlet.com" + a.find_all('a',href=True)[0]['href']
	        image_url = "https:" + a.find_all('img')[0]['src']
	        search_results += [[author,title,link_url,image_url]]
	return search_results