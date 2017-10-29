import requests
import sys, threading
from bs4 import BeautifulSoup, SoupStrainer
import lxml

getSignal=""
getPrice=""
getChange=""
getVolume=""

class CrawlerThread(threading.Thread):
    def __init__(self, binarySemaphore, ticker):
        self.binarySemaphore = binarySemaphore
        self.ticker = ticker
        self.threadId = hash(self)
        threading.Thread.__init__(self)

    def run(self):
        print ("Thread #%d: Reading from %s" + str(self.threadId))
        self.crawl_pages(self.ticker)
        self.binarySemaphore.release()

    def crawl_pages(self, ticker):
        global getSignal
        global getPrice
        global getChange
        global getVolume

        url="https://www.americanbulls.com/m/SignalPage.aspx?lang=en&Ticker="+str(ticker)
        source_code = requests.get(url)
        plain_text = source_code.text
        strainer = SoupStrainer('span',{'id': [ 'MainContent_LastSignal',
                                                'MainContent_Change',
                                                'MainContent_ChangePercent']})
        soup = BeautifulSoup(plain_text, "lxml", parse_only=strainer)
        getSignal = soup.find(id="MainContent_LastSignal").string
        change=soup.find(id="MainContent_Change").string
        percentchange=soup.find(id="MainContent_ChangePercent").string
        getChange = change+" ("+percentchange+")"

        url="https://www.stocktwits.com/symbol/"+str(ticker)
        source_code = requests.get(url)
        plain_text = source_code.text
        strainer = SoupStrainer('span',{'class': 'price'})
        soup = BeautifulSoup(plain_text, "lxml", parse_only=strainer)
        getPrice = soup.find(class_="price").string

        url="http://www.nasdaq.com/symbol/"+str(ticker)
        source_code = requests.get(url)
        plain_text = source_code.text
        strainer = SoupStrainer('label',{'id': str(ticker)+'_Volume'})
        soup = BeautifulSoup(plain_text, "lxml", parse_only=strainer)
        getVolume = soup.find(id=str(ticker).upper()+'_Volume').string


if __name__ == "__main__":
    binarySemaphore = threading.Semaphore(1)
    tickers = ["XXII","AAPL","BLDP","MNKD","PLUG","TSLA","FB"]
    for ticker in tickers:
        crawler = CrawlerThread(binarySemaphore, ticker).start()
        print(getSignal)
