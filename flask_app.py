from flask import Flask, render_template, request
import requests
import urllib.request
from bs4 import BeautifulSoup
from betterreads import client
import urllib.parse
import time

app = Flask(__name__)

@app.route("/", methods=['GET','POST'])
def home_view():
	if request.method == "GET":
		return render_template("redirect.html")
	user_id = int( request.form['user_id'] )
	valid_books,error,successful_processes,shelf_size = getBooks(user_id=user_id)
	successes = "Out of the " + str(shelf_size) + " books processed from your Goodreads to-read shelf, " + str( successful_processes ) + " are on Book Outlet"
	return render_template("main_page.html",books=valid_books,err=error,successes=successes )

def getBooks(user_id):
	api_key = "Eny1ro9b7mxhs8CuFj2o6w"
	api_secret = "bQKcvwYsv0ceEBjk95guDtguTXRUSgBxGPBT0YtxD6U"
	gc = client.GoodreadsClient(api_key, api_secret)
	user = gc.user(user_id)
	if 'private' in list(user.__dict__['_user_dict'].keys()) and user.__dict__['_user_dict']['private'] == 'true':
		return render_template("main_page.html",successes="Oops! Looks like your profile is on private. You can change this in Goodreads -> Account Settings -> Settings -> Privacy")
	#gr_books = user.per_shelf_reviews(shelf_name = "currently-reading")
	gr_books = user.per_shelf_reviews(shelf_name = "to-read")
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
		if time.time() - start > max_time:
			start_next = gr_books.index(book)
			leftover_books = gr_books[start_next:]
			break
	return valid_books,error,successful_processes,shelf_size,leftover_books

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
	    price = a.find('div','price').find_all(text=True)[0]
	    title = title.split("(")[0].strip()
	    form = a.find('p','small').find_all(text=True)[0]
	    form = form.replace(")","").replace("(","")
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
	        search_results += [[author,title,link_url,image_url,price,form]]
	return search_results