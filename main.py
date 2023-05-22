import requests
from bs4 import BeautifulSoup
import pdb
import json
from urllib.parse import urlencode, quote_plus
import sys
import sqlite3
import time
import tayph.util as ut
from tqdm import tqdm


#Read the API token:
with open('apikey.dat','r') as f:
    token = f.read()[:-1]

burl = "https://api.adsabs.harvard.edu/v1/search/"
entry = "2018Natur.560..453H"
entry = "2022NatAs...6..449P"


class paper:
    def __init__(self,entry,delay=0.3,from_SQL = '',verbose=False):
        """ This queries a paper from the API, or loads it from the SQL database."""
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
        self.verbose = verbose
        self.queried = False

        r = None
        if len(from_SQL) > 0:
            from_SQL = str(ut.check_path(from_SQL,exists=True))
            with sqlite3.connect(from_SQL) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM papers WHERE bibcode = ?',(self.bibcode,))
                r = cursor.fetchone()
        if r is not None:
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
            if len(from_SQL) > 0 and verbose: print(f'Paper {self.bibcode} not found in {from_SQL}. Querying. Did you run to_SQL?')

        if r is None:#If from_SQL was not set or if it was, but the paper was not found:
            time.sleep(self.delay)
            query = {"q": "bibcode:"+entry,"fl":"title,citation,abstract,reference,date,first_author,doi,pub,author,year"}
            encoded_query = urlencode(query)
            response = requests.get(burl+"query?{}".format(encoded_query),headers={'Authorization': 'Bearer ' + token})
            self.response = response

            if response.status_code == 200:
                result = response.json()['response']['docs'][0]
                try:
                    self.citations = result['citation']
                except KeyError:
                    self.citations = []
                try:
                    self.references = result['reference']
                except KeyError:
                    self.references = []
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
                self.queried = True


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
            if self.verbose:
                print(f'Adding/updating {self.bibcode} in {filename}.')
            cursor.execute('''
            REPLACE INTO papers (bibcode,title,abstract,firstauthor,authors,journal,date,ncitations,nreferences,citations,"references",year,bibtex)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (self.bibcode,self.title,self.abstract,self.firstauthor,';'.join(self.authors),self.journal,self.date,self.ncitations,self.nreferences,','.join(self.citations),','.join(self.references),self.year,self.bibtex))
            conn.commit()

def load_SQL(f='papers.db'):
    """
    This parses the entire SQL database in a list of paper objects.
    """
    f = ut.check_path(f,exists=True)
    # Connect to the SQLite database
    with sqlite3.connect(str(f)) as conn:
        cursor = conn.cursor()
        #Replace a row in the table
        cursor.execute('SELECT bibcode FROM papers')
        rows = cursor.fetchall()

    papers = []
    for p in rows:
        papers.append(paper(p[0],from_SQL=f))
    return(papers)






class crawler:
    def __init__(self,entry,depth=2,direction='past',database='papers.db',delay=0.4,verbose=True,demo=False,rate_minimum=500):
        """This is an object that will move through the tree in a certain direction
        (past or future. It will store all papers in the papers database.)
        """
        self.depth = depth
        self.direction = direction
        self.database = database
        self.delay = delay
        self.entry = entry
        self.verbose = verbose
        self.demo = demo
        self.papers_crawled = []

        self.rate_minimum = rate_minimum

        #This is to dermine the current rate limit:
        testpaper = paper(entry)
        self.current_rate = int(testpaper.response.headers['X-RateLimit-Remaining'])
        if self.current_rate < self.rate_minimum:
            raise Exception(f'Allowed remaining requests is too low! ({self.current_rate})')



        P = [self.entry]

        for i in range(self.depth):
            if self.verbose: print(f'Starting layer {i+1}')
            P = self.crawl_layer(P,demo=self.demo,verbose=self.verbose)
        self.P_final = P

    def get_paper(self,bc):
        """This searches a paper by its bibcode, first in the SQL table and then in the ADS."""
        P = paper(bc,from_SQL=self.database,delay=self.delay)
        if P.queried:
            #If it wasn't already in the database, we add it.
            P.to_SQL(filename=self.database)
            #And update the last known remaining requests.
            self.current_rate = int(P.response.headers['X-RateLimit-Remaining'])
            if self.current_rate < self.rate_minimum:
                raise Exception(f'Allowed remaining requests is too low! ({self.current_rate})')
        return(P)


    def crawl_layer(self,bc,direction='past',ignore_existing=True,verbose=True,demo=False):
        """This takes a list of bibcodes, queries the papers that the bibcodes correspond to,
        records the references (if crawling into the past) or citations (crawling into the
        future) and then queries those papers, which then get added to the SQL database with the
        get_paper method. The corresponding paper bibcodes are also returned. Which means that
        this function can take its own output as input, meaning that it can be used recursively.

        Set the ignore_existing keyword to ignore papers that are already in the SQL table.

        Set the dud keyword to only run the checks, but not the actual querying.
        """
        paper_feed = []
        new_papers = []

        if len(bc) == 0:
            return([])

        if direction == 'past':
            for p in bc:
                paper_feed+=self.get_paper(p).references
        if direction == 'future':
            for p in bc:
                paper_feed+=self.get_paper(p).citations
        if verbose:
            print(f'Crawling {len(paper_feed)} papers.')
        if ignore_existing:
            paper_feed_to_query = check_in_database(paper_feed,inverse=True)
            print(f'...of which {len(paper_feed_to_query)} are not yet in {self.database}.')
            if len(paper_feed) ==0:
                print('Skipping.')
                return([])
            print('Only these are queried.\n')
        else:
            paper_feed_to_query = paper_feed

        paper_feed_to_query_unique = list(set(paper_feed_to_query))
        if len(paper_feed_to_query) != len(paper_feed_to_query_unique) and verbose:
            print(f'{len(paper_feed_to_query)-len(paper_feed_to_query_unique)} duplicates ignored.')


        for bc2 in tqdm(paper_feed_to_query_unique,desc="Crawling",unit=" items"):
            if not demo:
                void = self.get_paper(bc2)
        self.papers_crawled.append(paper_feed)
        if verbose:
            print('Crawling complete. \n \n')
        return(paper_feed)


def check_in_database(bc,database='papers.db',inverse=False):
    """ This checks whether a list of bibcodes bc is present in the SQL table. It returns the ones
    that are. Set the inverse keyword to do the oppose: Return the ones that are *not* in the SQL
    table.

    Example:
    R = check_in_database(['2003JPCA..107.3728O','1999JPCA..103.3721R','1777JPCA..103.3721R'],inverse=True)
    """
    import tayph.util as ut
    import sqlite3
    if type(bc) == str:
        bc = [bc]
    query = "SELECT * FROM papers WHERE bibcode = ?"
    database=str(ut.check_path(database,exists=True))
    results = []
    with sqlite3.connect(database) as conn:
        cursor = conn.cursor()
        for p in bc:
            cursor.execute(query, (p,))
            if not inverse:
                if cursor.fetchone() is not None:
                    results.append(p)
            if inverse:
                if cursor.fetchone() is None:
                    results.append(p)
    return(results)



# P = paper(entry)

# for i in range(len(P.references)):
#     print(i)
#     PP = paper(P.references[i])
#     PP.to_SQL()



C = crawler(entry,depth=2)
pdb.set_trace()
