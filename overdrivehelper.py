import requests
import urllib.request
from bs4 import BeautifulSoup
import urllib.parse
import json

def libraryHas(title, author, root, only_available=False, ebooks=True, audiobooks=True):
    title = title.split(" (")[0]
    title_url = urllib.parse.quote_plus(title)
    #root = "https://bpl.overdrive.com/"
    url = root + "search?query=" + title_url
    #url = 'https://bpl.overdrive.com/search?query=a+court+of+thorns+and+roses'
    #print(url)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    script = soup.findAll('script')
    yikes_json = str( script[0].string )
    yikes_json = yikes_json.split("window.OverDrive.mediaItems = ")
    my_books = []
    if len(yikes_json) < 2:
        my_books += ["ERROR"]
        return my_books
    yikes_json = yikes_json[1]
    yikes_json = yikes_json.split("window.OverDrive.thunderHost")[0]
    if len(yikes_json) < 100:
        my_books += ["ERROR"]
        return my_books
    yikes_json = yikes_json.split("}};")[0] + "}}"
    books = json.loads(yikes_json)
    if books:
        for book in books:
            correct_title = False;
            correct_author = True;
            book_info = books[book]
            od_title = book_info["title"].lower()
            #print("od: " + od_title)
            od_author = book_info["firstCreatorName"].lower()
            available = book_info["isAvailable"]
            if "cover300Wide" in book_info["covers"]:
                image_url = book_info["covers"]["cover300Wide"]["href"]
            else:
                image_url = ""
            link_url = root + "media/" + book_info["id"]
            if only_available and (not available):
                continue
            booktype = book_info["type"]["name"]
            #print("ebooks and audiobooks = " + str(not (ebooks and audiobooks)))
            #print("ebooks = " + str(ebooks and not (booktype.lower() == "ebook")))
            if not (ebooks and audiobooks):
                #print(booktype.lower())
                if ebooks:
                    # print("type " + booktype.lower())
                    # print(booktype.lower() == "audiobook")
                    if booktype.lower() == "audiobook":
                        print("skipped")
                        continue
                if audiobooks:
                    if booktype.lower() == "ebook":
                        continue
            if( od_title == title.lower() ):
                correct_title = True
                #print(correct_title)
                nms = author.lower().split()
                for nm in nms:
                    #print(nm + " VS " + od_author)
                    if nm not in od_author:
                        correct_author = False
            if correct_title and correct_author:
                #hasBook = True
                my_books += [[author,title,link_url,image_url,available,booktype]]
                #print("True")
    return my_books