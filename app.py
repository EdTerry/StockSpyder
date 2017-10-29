from pymongo import MongoClient
from bson.objectid import ObjectId
from flask import Flask,render_template,jsonify,json,request
from IPython.display import display_html
from bs4 import BeautifulSoup, SoupStrainer

import sys, threading
import pymongo
import requests
import lxml

application = Flask(__name__)

client = MongoClient('localhost:27017')
db = client.TickerData
db.Tickers.create_index([('device', pymongo.ASCENDING)], unique=True)

#TODO: User database with login system

binarySemaphore = threading.Semaphore(20)

getSignal=""
getPrice=""
getChange=""
getVolume=""

@application.route("/addTicker",methods=['POST'])
def addTicker():
    try:
        json_data = request.json['info']
        deviceName = json_data['device']

        crawl_pages_nonmultithreaded(deviceName.upper())

        if ( getPrice == "" ):
            return jsonify(status='ERROR',message="Ticker not found in resources.")

        db.Tickers.insert_one({
            'device':deviceName.upper(),
            'signal':getSignal,
            'price':getPrice,
            'change':getChange,
            'volume':getVolume,
            })
        return jsonify(status='OK',message='inserted successfully')

    except Exception as e:
        return jsonify(status='ERROR',message=str(e))

@application.route('/')
def showTickerList():
    return render_template('list.html')

@application.route('/getTicker',methods=['POST'])
def getTicker():
    try:
        tickerId = request.json['id']
        ticker = db.Tickers.find_one({'_id':ObjectId(tickerId)})

        tickerDetail = {
                'device':ticker['device'].upper(),
                'signal':ticker['signal'],
                'price':ticker['price'],
                'change':ticker['change'],
                'volume':ticker['volume'],
                'id': tickerId
                }

        return json.dumps(tickerDetail)
    except Exception as e:
        return str(e)

@application.route('/updateTicker',methods=['POST'])
def updateTicker():
    try:
        tickerInfo = request.json['info']
        tickerId = tickerInfo['id']
        device = tickerInfo['device']

        crawl_pages_nonmultithreaded(device.upper())

        db.Tickers.update_one({'_id':ObjectId(tickerId)},
                            {'$set':{
                                'device':device.upper(),
                                'signal':getSignal,
                                'price':getPrice,
                                'change':getChange,
                                'volume':getVolume}})

        # CrawlerThread(binarySemaphore, device.upper(), tickerId).start()

        return jsonify(status='OK',message='updated successfully')
    except Exception as e:
        return jsonify(status='ERROR',message=str(e))

#Refresh Tickers
@application.route("/refreshTickers",methods=['POST'])
def refreshTickers():
    try:
        tickers = db.Tickers.find()

        tickerList = []
        for ticker in tickers:

            CrawlerThread(binarySemaphore, ticker['device'], ticker['_id']).start()

        return jsonify(status='OK',message='updated successfully')
    except Exception as e:
        return jsonify(status='ERROR',message=str(e))


@application.route("/getTickerList",methods=['POST'])
def getTickerList():
    try:
        tickers = db.Tickers.find()

        tickerList = []
        for ticker in tickers:

            # We don't crawl here because we've stored this info in MongoDB for
            # quickest retrieval or possible downtime from crawled sites.
            tickerItem = {
                    'device':ticker['device'].upper(),
                    'signal':ticker['signal'],
                    'price':ticker['price'],
                    'change':ticker['change'],
                    'volume':ticker['volume'],
                    'id': str(ticker['_id'])
                    }

            tickerList.append(tickerItem)
    except Exception as e:
        return str(e)
    return json.dumps(tickerList)

# Webcrawler -- Still in use within addTicker and updateTicker. Let's make the move.
def crawl_pages_nonmultithreaded(ticker):
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

@application.route("/deleteTicker",methods=['POST'])
def deleteTicker():
    try:
        tickerId = request.json['id']
        db.Tickers.remove({'_id':ObjectId(tickerId)})
        return jsonify(status='OK',message='deletion successful')
    except Exception as e:
        return jsonify(status='ERROR',message=str(e))


# New crawling method with multithreading
class CrawlerThread(threading.Thread):
    def __init__(self, binarySemaphore, ticker, tickerId):
        self.binarySemaphore = binarySemaphore
        self.ticker = ticker
        self.tickerId = tickerId
        self.threadId = hash(self)
        threading.Thread.__init__(self)

    def run(self):
        print ("Thread #%d: Reading from %s" + str(self.threadId))
        self.crawl_pages(self.ticker, self.tickerId)
        self.binarySemaphore.release()

    #Parameter to do diff things...
    def crawl_pages(self, ticker, tickerId):
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

        db.Tickers.update_one({'_id':ObjectId(self.tickerId)},
                            {'$set':{
                                'device':self.ticker.upper(),
                                'signal':getSignal,
                                'price':getPrice,
                                'change':getChange,
                                'volume':getVolume}})


if __name__ == "__main__":
    application.run(host='0.0.0.0')