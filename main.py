import requests
from bs4 import BeautifulSoup
import pdb
import json
from urllib.parse import urlencode, quote_plus
import sys
import sqlite3
import time



#Read the API token:
with open('apikey.dat','r') as f:
    token = f.read()[:-1]

burl = "https://api.adsabs.harvard.edu/v1/search/"
entry = "2018Natur.560..453H"



#Start the SQL database.
conn = sqlite3.connect('papers.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS papers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        firstauthor TEXT,
        journal TEXT,
        date TEXT,
        doi TEXT,
        adsurl TEXT UNIQUE,
        abstact TEXT
    )
''')

class paper:
    def __init__(self,entry,delay=0.2):
        self.bibcode = entry
        self.delay = delay
        self.title=''
        self.citations = []
        self.ncitations = 0
        self.references = []
        self.nreferences = 0
        self.date = ''
        self.firstauthor = ''
        self.journal = ''
        self.abstract = ''
        self.authors = ''
        self.n_authors = 0
        self.sleeptime = delay
        self.bibtex = ''
        self.year = 0



        time.sleep(self.delay)
        query = {"q": "bibcode:"+entry,"fl":"title,citation,abstract,reference,date,first_author,doi,pub,author,year"}
        encoded_query = urlencode(query)
        response = requests.get(burl+"query?{}".format(encoded_query),headers={'Authorization': 'Bearer ' + token})



        if response.status_code == 200:
            result = response.json()['response']['docs'][0]
            self.citations = result['citation']
            self.references = result['reference']
            self.nreferences = len(self.references)
            self.ncitations = len(self.citations)
            self.date = result['date']
            self.abstract = result['abstract']
            self.firstauthor = result['first_author']
            self.doi = result['doi']
            self.journal = result['pub']
            self.authors = result['author']
            self.qresponse = response.json()
            self.qresult = result
            self.year = result['year']

    def get_bibtex(self):
        time.sleep(self.delay)
        results = requests.get("https://api.adsabs.harvard.edu/v1/export/bibtex/"+self.bibcode,headers={'Authorization': 'Bearer ' + token})

        #Change the identifier to be equal to the bibcode.
        self.bibtex = results.text.replace('{'+self.bibcode+',','{'+self.firstauthor.split(',')[0]+str(self.year)+',').strip()


P = paper(entry)

pdb.set_trace()
# https://adsabs.net/cgi-bin/nph-data_query?bibcode=2022A&A...666A.118J&link_type=CITATIONS
