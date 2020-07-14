import requests
import urllib.request
from bs4 import BeautifulSoup
import urllib.parse

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