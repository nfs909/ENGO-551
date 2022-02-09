from textwrap import indent
import requests
import json
import re

api_key = 'AIzaSyCYeG_jysQkoGrS7Dld_qBvg92ge-gyss4'
isbn = '0061007226'
rp = requests.get("https://www.googleapis.com/books/v1/volumes?q={}&key={}".format(isbn,api_key))
r = rp.json()
rank = 0
for i in r['items']:
    isbn_val=str(i['volumeInfo']['industryIdentifiers'])
    ap = re.search(r"\b{}\b".format(str(isbn)), isbn_val, re.IGNORECASE)
    if ap is not None:
        break
    rank+=1

rating = r["items"][rank]['volumeInfo']['averageRating']
print(rating)

#rating = r["items"][0]['volumeInfo']['averageRating']
#print(json.dumps(r['items'], indent = 4))
