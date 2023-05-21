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


class paper:
    def __init__(self,entry,delay=0.3,from_SQL = ''):
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
        self.sleeptime = delay
        self.bibtex = ''
        self.year = 0

        if len(from_SQL) > 0:
            with sqlite3.connect(from_SQL) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM papers WHERE bibcode = ?',(self.bibcode,))
                r = cursor.fetchone()
                self.bibcode=r[1]
                self.title=r[2]
                self.abstract=r[3]
                self.firstauthor=r[4]
                self.authors=r[5].split(';')
                self.journal=r[6]
                self.date=r[7]
                self.ncitations=r[8]
                self.nreferences=r[9]
                self.citations=r[10].split(',')
                self.references=r[11].split(',')
                self.year=r[12]
                self.bibtex=r[13]
        else:
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
                self.date = str(result['date']).split('T')[0]
                try:
                    self.abstract = result['abstract']
                except:
                    pass
                self.firstauthor = result['first_author']
                # self.doi = result['doi']
                self.journal = result['pub']
                self.authors = result['author']
                self.year = int(result['year'])
    def print(self):
        print(f'{self.bibcode} - {self.firstauthor} et al.  - {self.title}')

    def get_bibtex(self):
        time.sleep(self.delay)
        results = requests.get("https://api.adsabs.harvard.edu/v1/export/bibtex/"+self.bibcode,headers={'Authorization': 'Bearer ' + token})
        #Change the identifier to be equal to the bibcode.
        self.bibtex = results.text.replace('{'+self.bibcode+',','{'+self.firstauthor.split(',')[0]+str(self.year)+',').strip()

    def to_SQL(self,filename='papers.db'):
        # Insert the information contaied in the paper object (p) into the SQL table.
        with sqlite3.connect(filename) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS papers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bibcode TEXT UNIQUE,
                    title TEXT,
                    abstract TEXT,
                    firstauthor TEXT,
                    authors TEXT,
                    journal TEXT,
                    date TEXT,
                    ncitations INTEGER,
                    nreferences INTEGER,
                    citations TEXT,
                    "references" TEXT,
                    year INTEGER,
                    bibtex TEXT
                )''')

            cursor.execute('''
            REPLACE INTO papers (bibcode,title,abstract,firstauthor,authors,journal,date,ncitations,nreferences,citations,"references",year,bibtex)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (self.bibcode,self.title,self.abstract,self.firstauthor,';'.join(self.authors),self.journal,self.date,self.ncitations,self.nreferences,','.join(self.citations),','.join(self.references),self.year,self.bibtex))
            conn.commit()

def load_SQL(f='papers.db'):
    """
    This parses the entire SQL database in a list of paper objects.
    """

    # Connect to the SQLite database
    with sqlite3.connect(f) as conn:
        cursor = conn.cursor()
        #Replace a row in the table
        cursor.execute('SELECT bibcode FROM papers')
        rows = cursor.fetchall()

    papers = []
    for p in rows:
        papers.append(paper(p[0],from_SQL=f))
    return(papers)






# P = paper(entry)

# for i in range(len(P.references)):
#     print(i)
#     PP = paper(P.references[i])
#     PP.to_SQL()

import tayph.util as ut
t1=ut.start()
P = load_SQL()
ut.end(t1)
pdb.set_trace()
