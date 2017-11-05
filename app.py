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

#TODO: User database with login system. Will probably require seperate lists per user.
#TODO:  In order to fix the issue with the list not updating, make tickerList global.
#       Then we append to tickerList and check for dups using 'if ITEM not in LIST'
finished = False
max_connections = 20
binarySemaphore = threading.Semaphore(max_connections)

getSignal=""
getPrice=""
getChange=""
getVolume=""

@application.route("/addTicker",methods=['POST'])
def addTicker():
    try:
        json_data = request.json['info']
        deviceName = json_data['device']

        CrawlerThread(binarySemaphore, deviceName.upper(), "", "add").start()

        return jsonify(status='OK',message='inserted successfully')
    except Exception as e:
        return jsonify(status='ERROR',message=str(e))

@application.route('/')
def showTickerList():
    global finished
    finished=False
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

        CrawlerThread(binarySemaphore, device.upper(), tickerId, "update").start()

        return jsonify(status='OK',message='updated successfully')
    except Exception as e:
        return jsonify(status='ERROR',message=str(e))


#Refresh Tickers
@application.route("/refreshTickers",methods=['POST'])
def refreshTickers():
    try:
        tickers = db.Tickers.find()

        for ticker in tickers:
            CrawlerThread(binarySemaphore, ticker['device'], ticker['_id'], "update").start()

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
    def __init__(self, binarySemaphore, ticker, tickerId, mode):
        #print("Init CrawlerThread")
        self.binarySemaphore = binarySemaphore
        self.ticker = ticker
        self.tickerId = tickerId
        self.mode = mode    #Update/Add
        self.threadId = hash(self)
        threading.Thread.__init__(self)

    def run(self):
        #print ("Thread #%d: Reading from %s" + str(self.threadId))
        self.crawl_pages(self.ticker, self.tickerId, self.mode)
        self.binarySemaphore.release()

    #Parameter to do diff things...
    def crawl_pages(self, ticker, tickerId, mode):
        url="https://www.americanbulls.com/m/SignalPage.aspx?lang=en&Ticker="+str(ticker)
        source_code = requests.get(url)
        plain_text = source_code.text
        strainer = SoupStrainer('span',{'id': 'MainContent_LastSignal'})
        soup = BeautifulSoup(plain_text, "lxml", parse_only=strainer)
        getSignal = soup.find(id="MainContent_LastSignal").string
        # change=soup.find(id="MainContent_Change").string
        # percentchange=soup.find(id="MainContent_ChangePercent").string
        # getChange = change+" ("+percentchange+")"

        # url="https://www.stocktwits.com/symbol/"+str(ticker)
        # source_code = requests.get(url)
        # plain_text = source_code.text
        # strainer = SoupStrainer('span',{'class': 'price'})
        # soup = BeautifulSoup(plain_text, "lxml", parse_only=strainer)
        # getPrice = soup.find(class_="price").string

        url="http://www.nasdaq.com/symbol/"+str(ticker)
        source_code = requests.get(url)
        plain_text = source_code.text
        strainer = SoupStrainer(['label',{'id': str(ticker)+'_Volume'},
                                'div',{'class': ['qwidget-cents qwidget-Green',
                                                'qwidget-cents qwidget-Red',
                                                'qwidget-percent qwidget-Green',
                                                'qwidget-percent qwidget-Red']},
                                'div',{'id':'qwidget_lastsale'}])
        soup = BeautifulSoup(plain_text, "lxml", parse_only=strainer)
        getVolume = soup.find(id=str(ticker).upper()+'_Volume').string
        getPrice = soup.find(id="qwidget_lastsale").string
        if ( soup.find(class_='qwidget-cents qwidget-Green') ):
            percent = soup.find(class_='qwidget-percent qwidget-Green').string
            change = soup.find(class_='qwidget-cents qwidget-Green').string
            change = str(round(float(change),3))
            getChange= "+"+change+" ("+percent+")"
        elif ( soup.find(class_='qwidget-cents qwidget-Red') ):
            percent = soup.find(class_='qwidget-percent qwidget-Red').string
            change = soup.find(class_='qwidget-cents qwidget-Red').string
            change = str(round(float(change),3))
            getChange= "-"+change+" ("+percent+")"

        # TODO: Refresh needs to happen here..
        global finished
        if ( self.mode == "update" ):
            print("Updating ticker: "+ticker)
            db.Tickers.update_one({'_id':ObjectId(self.tickerId)},
                                {'$set':{
                                    'device':self.ticker.upper(),
                                    'signal':getSignal,
                                    'price':getPrice,
                                    'change':getChange,
                                    'volume':getVolume}})

        #    finished=True
        elif ( self.mode == "add" ):
            print("Adding ticker: "+ticker)
            db.Tickers.insert_one({ 'device':self.ticker.upper(),
                                    'signal':getSignal,
                                    'price':getPrice,
                                    'change':getChange,
                                    'volume':getVolume})
        finished=True


@application.route("/status")
def getThreadStatus():
    with application.test_request_context():
        return jsonify(dict(status=('finished' if finished else 'running')))

if __name__ == "__main__":
    application.run(host='0.0.0.0')
