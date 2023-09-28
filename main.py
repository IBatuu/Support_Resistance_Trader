from __future__ import print_function
from ast import Pass
from cgi import print_environ, print_form
from tkinter.colorchooser import askcolor
import data as d
from email import message
from tkinter import EXCEPTION
from traceback import print_tb
from requests import Request, Session, Response
from threading import Thread
import _thread, json, websocket, requests, threading, itertools, time, math, random
from binance.spot import Spot   
import pandas as pd 
import plotly.graph_objects as chart
from datetime import datetime


client = Spot(key=d.nanceSubApi, secret=d.secretSubApi)
listenKey = client.new_isolated_margin_listen_key("BTCUSDT")
key = listenKey["listenKey"]

dfHigh = None
json1mMessage = None
jsonMessage = None
lastTradedPrice = None
previousTradedPrice = None
cancelBidId = None
cancelAskId = None
stopMargin = 65
bidAskMargin = 8
amountToBidAskBtc = None
stopLossTakenOut = False
btcusdt = "BTCUSDT"
maxAllowance = None
dfLow = None
lastTimeStamp = None

highResistances1m = []
lowResistances1m = []
alreadySweeped = None
timestamp = []
high = []
low = []
open = []
close = []
volume = []
openPositions = 0

def getLevels():
    global highResistances1m, lowResistances1m, lastTradedPrice, dfHigh, timestamp, high, low, open, close, volume, dfLow
    try:
        
        highResistances1m = []
        lowResistances1m = []

        url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=1"
        data = requests.get(url).json()

        startTime = int(data[0][0]) - 60000 * 1000 * 43
        lastTradedPrice = float(data[0][4])

        for numbers in range(0, 43):
            #datesToLoop.append(startTime)
            url = f"https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=1000&startTime={startTime}"
            data = requests.get(url).json()
            for kline in data:
                timestamp.append(int(kline[0])) 
                open.append(float(kline[1]))
                high.append(float(kline[2])) 
                low.append(float(kline[3])) 
                close.append(float(kline[4]))
                volume.append(float(kline[5]))
            nextTime = 60000 * 1000 + startTime
            startTime = nextTime

        priceIndex = 0
        for price in high:
            priceIndex += 1
            score = 0
            for highest in high[priceIndex:]:
                if price >= highest:
                    score += 1
                    if score >= 150:
                        if price not in highResistances1m:
                            if highResistances1m == []:
                                highResistances1m.append(price)
                            else:          
                                for highResistance in highResistances1m:
                                    if abs(price - highResistance) <= 20:
                                        tooClose = True
                                if tooClose == False:
                                    highResistances1m.append(price)    
                else:
                    if price in highResistances1m:
                        highResistances1m.remove(price)
                    break
            tooClose = False
        priceIndex = 0
        for lowPrice in low:
            priceIndex += 1
            score = 0
            for lowest in low[priceIndex:]:
                if lowPrice <= lowest:
                    score += 1
                    if score >= 150:
                        if lowPrice not in lowResistances1m:
                            if lowResistances1m == []:
                                lowResistances1m.append(lowPrice)
                            else:          
                                for highResistance in lowResistances1m:
                                    if abs(lowPrice - highResistance) <= 20:
                                        tooClose = True
                                if tooClose == False:
                                    lowResistances1m.append(lowPrice)    
                else:
                    if lowPrice in lowResistances1m:
                        lowResistances1m.remove(lowPrice)
                    break
            tooClose = False
        print(highResistances1m)
        print(lowResistances1m)

    except Exception as e:
        print(e)
        pass
getLevels()

def wsUserData(ws, message):
    global stopMargin, bidAskMargin, stopLossTakenOut, filledPrice, filledSide, filledQuantity, priceToBid, bidToStop, stopLimitbid, priceToAsk, askToStop, stopLimitask, openPositions
    jsonMessage = json.loads(message)
    print(jsonMessage)
    if jsonMessage["e"] == "executionReport":
        if jsonMessage["x"] == "TRADE":
            if jsonMessage["X"] == "FILLED":
                if jsonMessage["o"] == "LIMIT":
                    openPositions += 1
                    filledPrice = round(float(jsonMessage["L"]))
                    filledSide = jsonMessage["S"]
                    filledQuantity = float(jsonMessage["z"])
                    priceToBid = round(filledPrice * 0.998, 2)
                    bidToStop = round(filledPrice * 1.002, 2)
                    stopLimitbid = bidToStop + 20
                    priceToAsk = round(filledPrice * 1.002, 2)
                    askToStop = round(filledPrice * 0.998, 2)
                    stopLimitask = askToStop - 20
                    if filledSide == "SELL":
                        btcusdtbidParams = {
                        'symbol': 'BTCUSDT',
                        'side': 'BUY',
                        'quantity': filledQuantity,
                        'price': priceToBid,
                        'stopPrice': bidToStop,
                        'stopLimitPrice': stopLimitbid,
                        'stopLimitTimeInForce': 'GTC',
                        'isIsolated': 'TRUE',
                        'sideEffectType': 'AUTO_REPAY'
                        }
                        try:
                            oco1 = client.new_margin_oco_order(**btcusdtbidParams)
                        except Exception as e:
                            print(e)
                            time.sleep(2)
                            oco1 = client.new_margin_oco_order(**btcusdtbidParams)
                            pass
                    if filledSide == "BUY":
                        btcusdtaskParams = {
                        'symbol': 'BTCUSDT',
                        'side': 'SELL',
                        'quantity': filledQuantity,
                        'price': priceToAsk,
                        'stopPrice': askToStop,
                        'stopLimitPrice': stopLimitask,
                        'stopLimitTimeInForce': 'GTC',
                        'isIsolated': 'TRUE',
                        'sideEffectType': 'AUTO_REPAY'
                        }
                        try:
                            oco2 = client.new_margin_oco_order(**btcusdtaskParams)
                        except Exception as e:
                            print(e)
                            time.sleep(2)
                            oco2 = client.new_margin_oco_order(**btcusdtaskParams)
                            pass
def wsUserDataThread(*args):
    socket = f"wss://stream.binance.com:9443/ws/{key}"
    ws = websocket.WebSocketApp(socket, on_message=wsUserData)
    ws.run_forever(ping_interval=15, ping_payload=str({'op': 'ping'}))    
def keepAlive(*args):
    while True:
        time.sleep(60)
        client.renew_isolated_margin_listen_key(listenKey=key, symbol="BTCUSDT")
def bid(price, size):
    btcusdtbidParams = {
            'symbol': 'BTCUSDT',
            'side': 'BUY',
            'type': 'LIMIT',
            'timeInForce': 'GTC',
            'quantity': size,
            'price': price,
            'isIsolated': 'TRUE',
            'sideEffectType': 'MARGIN_BUY'
        }
    try:
        response1 = client.new_margin_order(**btcusdtbidParams)
        #cancelBidId = response1["orderId"]
        #print(response1)
    except Exception as e:
        print(e)
        pass
def ask(price, size):
    btcusdtaskParams = {
            'symbol': 'BTCUSDT',
            'side': 'SELL',
            'type': 'LIMIT',
            'timeInForce': 'GTC',
            'quantity': size,
            'price': price,
            'isIsolated': 'TRUE',
            'sideEffectType': 'MARGIN_BUY'
        }
    try:
        response2 = client.new_margin_order(**btcusdtaskParams)
        #cancelAskId = response2["orderId"]
        #print(response2)
    except Exception as e:
        print(e)
        pass
def checkForNakedPositions():
    global maxAllowance, lastTradedPrice, openPositions
    while True:
        try:
            accountInfo = client.isolated_margin_account(symbols="BTCUSDT")
            for asset in accountInfo["assets"]:
                if asset['baseAsset']["asset"] == "BTC":
                    borrowedBtc = float(asset['baseAsset']["borrowed"])
                    btcNetAssets = float(asset['baseAsset']["netAsset"])
                    freeBtc = float(asset["baseAsset"]["free"])
                    if freeBtc > 0.01:
                        time.sleep(5)
                        accountInfo = client.isolated_margin_account(symbols="BTCUSDT")
                        for asset in accountInfo["assets"]:
                            if asset['baseAsset']["asset"] == "BTC":
                                freeBtc = float(asset["baseAsset"]["free"])
                                if freeBtc > 0.01:
                                    amountToMarketSell = round(freeBtc - 0.0001, 4)
                                    btcusdtMarketSell = {
                                        'symbol': 'BTCUSDT',
                                        'side': 'SELL',
                                        'type': 'MARKET',
                                        'quantity': amountToMarketSell,
                                        'isIsolated': 'TRUE',
                                        'sideEffectType': 'AUTO_REPAY'
                                    }
                                    try:
                                        response6 = client.new_margin_order(**btcusdtMarketSell)
                                    except Exception as e:
                                        print(e)
                                        pass
                if asset['quoteAsset']["asset"] == "USDT":
                    freeUsdt = float(asset["quoteAsset"]["free"])
                    borrowedUsdt = float(asset['quoteAsset']["borrowed"])
                    usdtNetAssets = float(asset['quoteAsset']["netAsset"])
                    usdtNetAssetsBtc = float(asset['quoteAsset']["netAssetOfBtc"])
                    netAssets = btcNetAssets + usdtNetAssetsBtc
                    netAccountCapital = usdtNetAssets + btcNetAssets
                    if borrowedUsdt > 100:
                        if freeUsdt > 100:
                            time.sleep(5)
                            accountInfo = client.isolated_margin_account(symbols="BTCUSDT")
                            for asset in accountInfo["assets"]:
                                if asset['quoteAsset']["asset"] == "USDT":
                                    freeUsdt = float(asset["quoteAsset"]["free"])
                                    borrowedUsdt = float(asset['quoteAsset']["borrowed"])
                                    usdtNetAssets = float(asset['quoteAsset']["netAsset"])
                                    netAccountCapital = usdtNetAssets + btcNetAssets    
                                    if borrowedUsdt > 100:
                                        if freeUsdt > 100:
                                            excessAmount = round(freeUsdt - 10)
                                            print(excessAmount)
                                            amountToMarketBuy = round(excessAmount / lastTradedPrice, 3)
                                            print(amountToMarketBuy)
                                            btcusdtMarketBuy = {
                                                'symbol': 'BTCUSDT',
                                                'side': 'BUY',
                                                'type': 'MARKET',
                                                'quantity': amountToMarketBuy,
                                                'isIsolated': 'TRUE',
                                                'sideEffectType': 'AUTO_REPAY'
                                            }
                                            try:
                                                response7 = client.new_margin_order(**btcusdtMarketBuy)
                                            except Exception as e:
                                                print(e)
                                                pass
                    if freeUsdt > (netAssets * lastTradedPrice) + 200:
                            time.sleep(5)
                            accountInfo = client.isolated_margin_account(symbols="BTCUSDT")
                            for asset in accountInfo["assets"]:
                                if asset['quoteAsset']["asset"] == "USDT":
                                    freeUsdt = float(asset["quoteAsset"]["free"])
                                    borrowedUsdt = float(asset['quoteAsset']["borrowed"])
                                    usdtNetAssets = float(asset['quoteAsset']["netAsset"])
                                    usdtNetAssetsBtc = float(asset['quoteAsset']["netAssetOfBtc"])
                                    netAccountCapital = usdtNetAssetsBtc + btcNetAssets
                                    if freeUsdt > (netAssets * lastTradedPrice) + 200:   
                                            netAssets = btcNetAssets + usdtNetAssetsBtc
                                            buyAmount =  round(freeUsdt - round(netAssets * lastTradedPrice))
                                            print(netAssets)
                                            amountToMarketBuy = round(buyAmount / lastTradedPrice, 3)
                                            print(amountToMarketBuy)
                                            btcusdtMarketBuy = {
                                                'symbol': 'BTCUSDT',
                                                'side': 'BUY',
                                                'type': 'MARKET',
                                                'quantity': amountToMarketBuy,
                                                'isIsolated': 'TRUE',
                                                'sideEffectType': 'AUTO_REPAY'
                                            }
                                            try:
                                                response7 = client.new_margin_order(**btcusdtMarketBuy)
                                            except Exception as e:
                                                print(e)
                                                pass
            openOrders = client.margin_open_orders(symbol="BTCUSDT", isIsolated="TRUE")
            try:
                openOrders = client.margin_open_orders(symbol="BTCUSDT", isIsolated="TRUE")
                openPositions = 0
                for order in openOrders:
                    if order["type"] == "LIMIT":
                        orderTime = int(order["time"])
                        expiryTime = 60000 * 150 + orderTime
                        if lastTimeStamp > expiryTime:
                            client.cancel_margin_order(symbol="BTCUSDT", orderId=order["orderId"], isIsolated="TRUE")
                    if order["type"] == "LIMIT_MAKER":
                        openPositions += 1
            except Exception as e:
                print(e)
                pass
        except Exception as e:
            print(e)
            pass
        time.sleep(15)
def kline1mWsOpen(ws):
    subscribe_message = {
        "method": "SUBSCRIBE",
        "params":
            [
                "btcusdt@kline_1m",
            ],
        "id": 1
    }

    ws.send(json.dumps(subscribe_message))
    print("1m Kline Opened")
def kline1mMessage(ws, message):
    global json1mMessage, dfHigh, dfLow, timestamp, open, high, low, close, volume, highResistances1m, lowResistances1m, lastTradedPrice, lastTimeStamp
    json1mMessage = json.loads(message)
    lastTradedPrice = float(json1mMessage["k"]["c"])
    lastTimeStamp = int(json1mMessage["k"]["t"])
    tooClose = False
    if json1mMessage["k"]["x"] == True:
        try:
            timestamp.append(int(json1mMessage["k"]["t"])) #timestamp.append(str(datetime.fromtimestamp(int(kline[0])/1000, tz=None).strftime('%Y-%m-%d %H.%M.%S')))
            open.append(float(json1mMessage["k"]["o"]))
            high.append(float(json1mMessage["k"]["h"])) 
            low.append(float(json1mMessage["k"]["l"])) 
            close.append(float(json1mMessage["k"]["c"]))
            volume.append(float(json1mMessage["k"]["v"]))

            if len(high) > 151:
                highDifference = abs(len(high) - 151)
                high = high[highDifference:]
                timestamp = timestamp[highDifference:]
                open = open[highDifference:]
                low = low[highDifference:]
                close = close[highDifference:]
                volume = volume[highDifference:]

            priceIndex = 0
            for price in high:
                priceIndex += 1
                for highRes in highResistances1m:
                    if price >= highRes:
                        highResistances1m.remove(highRes)  
                score = 0
                for highest in high[priceIndex:]:
                    if price >= highest:
                        score += 1
                        if score >= 150:
                            if price not in highResistances1m:
                                if highResistances1m == []:
                                    highResistances1m.append(price)
                                else:          
                                    for highResistance in highResistances1m:
                                        if abs(price - highResistance) <= 20:
                                            tooClose = True
                                    if tooClose == False:
                                        highResistances1m.append(price)    
                    else:
                        if price in highResistances1m:
                            highResistances1m.remove(price)
                        break
                tooClose = False
            
            if len(low) > 151:
                lowDifference = abs(len(low) - 151)
                low = high[lowDifference:]
                timestamp = timestamp[lowDifference:]
                open = open[lowDifference:]
                low = low[lowDifference:]
                close = close[lowDifference:]
                volume = volume[lowDifference:]

            priceIndex = 0
            for lowPrice in low:
                priceIndex += 1
                for lowRes in lowResistances1m:
                    if lowRes >= lowPrice:
                        lowResistances1m.remove(lowRes)
                score = 0
                for lowest in low[priceIndex:]:
                    if lowPrice <= lowest:
                        score += 1
                        if score >= 150:
                            if lowPrice not in lowResistances1m:
                                if lowResistances1m == []:
                                    lowResistances1m.append(lowPrice)
                                else:          
                                    for lowResistance in lowResistances1m:
                                        if abs(lowPrice - lowResistance) <= 20:
                                            tooClose = True
                                    if tooClose == False:
                                        lowResistances1m.append(lowPrice)    
                    else:
                        if lowPrice in lowResistances1m:
                            lowResistances1m.remove(lowPrice)
                        break
                tooClose = False
            
            sortedHighs = sorted(highResistances1m)
            sortedLows = sorted(lowResistances1m)
            print("High List:", sortedHighs)
            print("Low List:", sortedLows)
            print("Number of Open Positions:", openPositions)
        except Exception as e:
            print(e)
            pass
def wsKline1mThread(*args):
    socket = "wss://stream.binance.com:9443/ws"
    ws = websocket.WebSocketApp(socket, on_open=kline1mWsOpen, on_message=kline1mMessage)
    ws.run_forever(ping_interval=15, ping_payload=str({'op': 'ping'}))

_thread.start_new_thread(wsUserDataThread, ())
_thread.start_new_thread(keepAlive, ())
_thread.start_new_thread(checkForNakedPositions, ())
_thread.start_new_thread(wsKline1mThread, ())

while True:
    try:
        bidAskSize = round((1000 * 1)/float(lastTradedPrice), 4)
        maxAllowance = bidAskSize * 1.2
        maxAllowanceUsdt = bidAskSize * 1.2 * lastTradedPrice
        for highResistance in highResistances1m:
            if lastTradedPrice >= highResistance:
                highResistances1m.remove(highResistance)
                if openPositions < 1:
                    ask(price=lastTradedPrice + round(lastTradedPrice * 0.0005), size=bidAskSize)
        for lowResistance in lowResistances1m:
            if lastTradedPrice <= lowResistance:
                lowResistances1m.remove(lowResistance)
                if openPositions < 1:
                    bid(price=lastTradedPrice - round(lastTradedPrice * 0.0005), size=bidAskSize)
    except Exception as e:
        print(e)
        pass
    
