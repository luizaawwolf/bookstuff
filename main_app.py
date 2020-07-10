from flask import Flask, render_template, request, redirect, url_for
import requests
import urllib.request
from bs4 import BeautifulSoup
from betterreads import client
import urllib.parse
import time
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

db = SQLAlchemy(app)
SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    username="annaluizabr",
    password="pythonanywhere",
    hostname="annaluizabr.mysql.pythonanywhere-services.com",
    databasename="annaluizabr$bookishbuys",
)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

class Subscription(db.Model):
    __tablename__ = "subscriptions"
    subscriber_id = db.Column(db.Integer, ForeignKey('subscribers.id'), primary_key=True)
    book_id = db.Column(db.Integer, ForeignKey('books.id'), primary_key=True)

class Book(db.Model):
    __tablename__ = "books"
    id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(500))
    author = db.Column(db.String(500))
    subscribers = relationship('Subscriber',secondary='subscriptions')

class Subscriber(db.Model):
    __tablename__ = "subscribers"
    id = db.Column(db.Integer,primary_key=True)
    email = db.Column(db.String(500))
    goodreads_id = db.Column(db.Integer)
    alert_on_new = db.Column(db.Boolean)
    alert_on_loss = db.Column(db.Boolean)
    books = relationship('Book',secondary='subscriptions')


@app.route("/feedback",methods=['GET','POST'])
def getPage():
    return render_template("feedback.html")

@app.route("/", methods=['GET','POST'])
def home_view():
	if request.method == "GET":
		return render_template("main_page.html")
	user_id = int( request.form['user_id'] )
	to_read = bool( request.form.getlist('toread') )
	read = bool( request.form.getlist('read') )
	valid_books,error,successful_processes,shelf_size = getBooks(user_id=user_id,to_read=to_read,read=read)
	if shelf_size == -1:
	    return render_template("main_page.html",successes="Oops! Looks like your profile is on private. You can change this in Goodreads -> Account Settings -> Settings -> Privacy")
	shelfs = ""
	if to_read and read:
		shelfs = "to-read and read shelf, "
	elif to_read:
		shelfs = "to-read shelf, "
	else:
		shelfs = "read shelf, "
	successes = "Out of the " + str(shelf_size) + " books processed from your Goodreads " + shelfs + str( successful_processes ) + " are on Book Outlet"
	return render_template("main_page.html",books=valid_books,err=error,successes=successes )

def getBooks(user_id,to_read,read):
	api_key = "Eny1ro9b7mxhs8CuFj2o6w"
	api_secret = "bQKcvwYsv0ceEBjk95guDtguTXRUSgBxGPBT0YtxD6U"
	gc = client.GoodreadsClient(api_key, api_secret)
	user = gc.user(user_id)
	if 'private' in list(user.__dict__['_user_dict'].keys()) and user.__dict__['_user_dict']['private'] == 'true':
	    print("PRIVATE")
	    return [],[],[],-1
	#gr_books = user.per_shelf_reviews(shelf_name = "currently-reading")
	gr_books = []
	if to_read:
		gr_books += user.per_shelf_reviews(shelf_name = "to-read")
	if read:
		gr_books += user.per_shelf_reviews(shelf_name = "read")
	valid_books,error,successful_processes,shelf_size,leftover_books=getBooksHelper(gr_books)
	return valid_books,error,successful_processes,shelf_size

def getBooksHelper(gr_books):
	valid_books = []
	error=False
	successful_processes = 0
	shelf_size = 0
	run_again = False
	max_time = 2.8 * 60
	start = time.time()
	leftover_books = []
	for book in gr_books:
		temp_book = book.book
		title = temp_book["title"]
		author = temp_book["authors"]["author"]["name"]
		results = bookOutletHas(title=title, author=author)
		if results:
			if results[0] == "ERROR":
			    error=True
			    continue
			else:
			    successful_processes += 1

		if results:
			for result in results:
				valid_books += [result]
				print(result)
		shelf_size += 1
		if time.time() - start > max_time:
			start_next = gr_books.index(book)
			leftover_books = gr_books[start_next:]
			print("TIMEOUT... BREAKING")
			break
	return valid_books,error,successful_processes,shelf_size,leftover_books

def bookOutletHas(title, author):
	title = title.split(" (")[0]
	#print("Checking " + title)
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
	    price = a.find('div','price').find_all(text=True)[0]
	    title = title.split("(")[0].strip()
	    form = a.find('p','small').find_all(text=True)[0]
	    form = form.replace(")","").replace("(","")
	    if title.lower() == ret_title.lower():
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
	        search_results += [[author,title,link_url,image_url,price,form]]
	return search_results

# @app.route("/subscribe", methods=['GET','POST'])
# def subscribe():
#     if request.method == 'GET':
#         return render_template('subscribe.html')
#     goodreads_id=request.form['user_id']
#     user_email=request.form['user_email']
#     alert_on_new=bool( request.form.getlist('alert_on_new') )
#     alert_on_loss=bool( request.form.getlist('alert_on_loss') )
#     subscriber=Subscriber(email=user_email,goodreads_id=goodreads_id,alert_on_new=alert_on_new,alert_on_loss=alert_on_loss)
#     print("MADE SUBSCRIBER...")
#     to_read_shelf = True    #allow input later
#     read_shelf = False  #allow input later
#     print("GETTING BOOKS...")
#     subscribers_books = getBooks(goodreads_id, to_read_shelf, read_shelf)[0]
#     for book in subscribers_books:
#         exists = db.session.query(Book.id).filter_by(title=book[1]).scalar()
#         obj =  db.session.query(Book).filter_by(title=book[1]).first()
#         dbHas = (exists != None)
#         subscribers_books = db.session.query(Book.title,Book.author).filter(Subscription.subscriber_id == subscriber.id, Book.id == Subscription.book_id).all()
#         userHas = (book[1],book[0]) in subscribers_books
#         if userHas:
#             continue
#         elif dbHas:
#             subscriber.books.append(obj)
#             db.session.add(subscriber)
#         else:
#             temp_book = Book(title=book[1],author=book[0])
#             db.session.add(temp_book)
#             db.session.add(subscriber)
#             subscriber.books.append(temp_book)
#     print("FINISHED GETTING BOOKS...")
#     db.session.add(subscriber)
#     db.session.commit()
#     send_email("Thanks for subscribing!","You've subscribed to receive updates from Bookish Buys. To unsubscribe, ",user_email)
#     return render_template('subscribe.html')

# def send_email(subject,texttosend,recipient):
#     port = 465  # For SSL
#     smtp_server = "smtp.gmail.com"
#     sender_email = "neverfullybooked@gmail.com"  # Enter your address
#     receiver_email = recipient  # Enter receiver address
#     password = "PythonAnywhere!"
#     message = MIMEMultipart("alternative")
#     message["Subject"] = subject
#     message["From"] = "Bookish Buys"
#     message["To"] = receiver_email

#     text = texttosend
#     html = """\
#     <html>
#       <body>
#         <p>""" + texttosend + """\
#         </p>
#       </body>
#     </html>
#     """
#     # Turn these into plain/html MIMEText objects
#     part1 = MIMEText(text, "plain")
#     part2 = MIMEText(html, "html")

#     # Add HTML/plain-text parts to MIMEMultipart message
#     # The email client will try to render the last part first
#     message.attach(part1)
#     message.attach(part2)

#     # Create secure connection with server and send email
#     context = ssl.create_default_context()
#     with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
#         server.login(sender_email, password)
#         server.sendmail(
#             sender_email, receiver_email, message.as_string()
#         )

# @app.route("/unsubscribe/<user_email>", methods=['GET','POST'])
# def unsubscribe(user_email):
#     subscribers =  db.session.query(Subscriber).filter_by(email=user_email)
#     for subscriber in subscribers:
#         subscriptions = db.session.query(Subscription).filter_by(subscriber_id=subscriber.id)
#         subscriptions.delete()
#     subscribers.delete()
#     db.session.commit()
#     return render_template("unsubscribed.html")

# @app.route("/check")
# #where subscriber is the subscriber object
# def loadstuff(user_email):
#     subscribers =  db.session.query(Subscriber).filter_by(email=user_email)
#     for subscriber in subscribers:
#         print(subscriber.id)
#         subscribers_books = db.session.query(Book.title,Book.author).filter(Subscription.subscriber_id == subscriber.id, Book.id == Subscription.book_id).all()
#         print(um)

# @app.route("/check/<user_id>")
# def check_differences(user_id):
#     subscriber = db.session.query(Subscriber).filter_by(id=user_id).first()
#     updated_books = getBooks(subscriber.goodreads_id,True,False)[0]    #to_read = True, read = False
#     subscribers_books = db.session.query(Book.title,Book.author).filter(Subscription.subscriber_id == subscriber.id, Book.id == Subscription.book_id).all()
#     send = False
#     for book in updated_books:
#         title_up = book[1]
#         author_up = book[0]
#         entry_search = (title_up,author_up)
#         in_database = entry_search in subscribers_books
#         if not in_database:
#             send = True
#             new_book_obj = Book(title=title_up,author=author_up)
#             subscriber.books.append(new_book_obj)
#     if send:
#         db.session.commit()
#         send_email("Good news for you!","There's been a new match between Book Outlet and your Goodreads to-read shelf. Go check it out!", subscriber.email)



#TODO:
#[X] CONFIGURE TO BE ABLE TO SEND EMAILS
#   [X] SEND WELCOME EMAIL
#   [X] CONFIGURE UNSUBSCRIBE
#[] WRITE METHOD TO CHECK FOR DIFFERENCE IN SHELFXBOOKOUTLET LIST
#   - GET LIST OF SUBSCRIBER'S CURRENT BOOKS
#   - GET LIST FROM getBooks
#   - IF LIST DIFFERS, SEND EMAIL
#[] UPDATE TO ONLY ALERT ON NEW
#[] FIGURE OUT HOW TO RUN THE METHOD EVERY NIGHT FOR EVERY SUBSCRIBER