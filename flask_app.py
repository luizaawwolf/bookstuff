from flask import Flask, render_template, request
import requests
import urllib.request
from bs4 import BeautifulSoup
from betterreads import client
import urllib.parse
import time
from bookoutlethelper import bookOutletHas
from overdrivehelper import libraryHas

app = Flask(__name__)

@app.route("/", methods=['GET','POST'])
def home_view():
	if request.method == "GET":
		return render_template("main_page.html")
	user_id = int( request.form['user_id'] )
	to_read = bool( request.form.getlist('toread') )
	read = bool( request.form.getlist('read') )
	valid_books,error,successful_processes,shelf_size = getBooks(user_id=user_id,to_read=to_read,read=read,source="bookoutlet")
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

def getBooks(user_id,to_read,read,source,extras=[]):
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
	if source == "bookoutlet":
		valid_books,error,successful_processes,shelf_size,leftover_books=getBooksHelper(gr_books,source)
		return valid_books,error,successful_processes,shelf_size
	if source == "overdrive":
		valid_books,error,successful_processes,shelf_size,leftover_books=getBooksHelper(gr_books,source,extras)
		return valid_books,error,successful_processes,shelf_size,leftover_books

def getBooksHelper(gr_books,source,extras=[]):
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
		if source == "bookoutlet":
			results = bookOutletHas(title=title, author=author)
		if source == "overdrive":
			available=extras[0]
			ebooks=extras[1]
			audiobooks=extras[2]
			root = extras[3]
			results = libraryHas(title=title, author=author, root=root,only_available=available,ebooks=ebooks,audiobooks=audiobooks)
		if results:
			if results[0] == "ERROR":
			    error=True
			    continue
			else:
			    successful_processes += 1

		if results:
			for result in results:
				valid_books += [result]
				#print(result)
		shelf_size += 1
		if time.time() - start > max_time:
			start_next = gr_books.index(book)
			leftover_books = gr_books[start_next:]
			print("TIMEOUT... BREAKING")
			break
	return valid_books,error,successful_processes,shelf_size,leftover_books

@app.route("/overdrive", methods=['GET','POST'])
def ov_view():
	if request.method == "GET":
		return render_template("overdrivepage.html")
	user_id = int( request.form['user_id'] )
	to_read = bool( request.form.getlist('toread') )
	read = bool( request.form.getlist('read') )
	only_available = bool( request.form.getlist('available') )
	ebooks = bool( request.form.getlist('ebooks') )
	audiobooks = bool( request.form.getlist('audiobooks') )
	lib_url = request.form['lib_url']
	lib_name = lib_url.split(".overdrive.com")[0].split("//")[1]
	root = "https://" + lib_name + ".overdrive.com/"
	#valid_books,error,successful_processes,shelf_size = 
	valid_books,error,successful_processes,shelf_size,leftover_books = getBooks(user_id=user_id,to_read=to_read,read=read,source="overdrive",extras=[only_available,ebooks,audiobooks,root])
	#print(valid_books)
	if shelf_size == -1:
	    return render_template("main_page.html",successes="Oops! Looks like your profile is on private. You can change this in Goodreads -> Account Settings -> Settings -> Privacy")
	shelfs = ""
	if to_read and read:
		shelfs = "to-read and read shelf, "
	elif to_read:
		shelfs = "to-read shelf, "
	else:
		shelfs = "read shelf, "
	successes = "Out of the " + str(shelf_size) + " books processed from your Goodreads " + shelfs + str( successful_processes ) + " are on Overdrive"
	return render_template("overdrivepage.html",books=valid_books,err=error,successes=successes)
	#return render_template("main_page.html",books=valid_books,err=error,successes=successes )