import ccxt
import time
import datetime
import pandas as pd
import math
import requests
import pprint

api_key = "change"
secret = "change"
binance = ccxt.binance(config={'apiKey':api_key,'secret':secret,'enableRateLimit':True,'options':{'defaultType':'future'}})

markets = binance.load_markets()
symbol = "BTC/USDT"
market = binance.market(symbol)
resp = binance.fapiPrivate_post_leverage({'symbol':market['id'],'leverage':4})

# 목표가 계산
def cal_target(symbol):
    btc_ohlcv = binance.fetch_ohlcv(symbol=symbol, timeframe='1d', since=None, limit=10)

    df = pd.DataFrame(data=btc_ohlcv, columns=['datetime','open','high','low','close','volums'])
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    df.set_index('datetime', inplace=True)

    yesterday = df.iloc[-2]
    today = df.iloc[-1]
    target = today['open'] + (yesterday['high'] - yesterday['low']) * 0.6
    return target

target = cal_target(symbol)

# 수량 계산
def cal_amount(usdt_balance, cur_price):
    portion = 1
    usdt_trade = usdt_balance * portion
    amount = math.floor((usdt_trade * 1000000)/cur_price)/1000000 * 3.9
    return amount


# 잔고 계산
balance = binance.fetch_balance()
usdt = balance['total']['USDT']

# 포지션 정보
position = {"type":None,"amount":0}

# 슬랙 설정
def post_message(token, channel, text):
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text}
    )
    print(response)
 
myToken = "xoxb-2196652603604-2214145924800-ockR6ovnPcrXyr3iwXI5Nbop"




# 매수 매도
def enter_position(binance,symbol,cur_price,target,amount,position):
    if cur_price > target:
        position['type'] = 'long'
        position['amount'] = amount
        binance.create_matket_buy_order(symbol=symbol, amount=amount)
        post_message(myToken,"#autotrade",str(cur_price)+" : 매수 완료")

def exit_position(binance, symbol, position):
    amount = position['amount']
    if position['type'] == 'long':
        binance.create_market_sel_order(symbol=symbol, amount=amount)
        position['type'] = None
        post_message(myToken,"#autotrade",str(cur_price)+" : 매도 완료")

op_mode = False


while True:
    # 현재 시간 조회
    now = datetime.datetime.now()
    
    # 포지션 청산
    if now.hour == 8 and now.minute == 50 and (0 <= now.second < 10):
        if op_mode and position['type'] is not None:
            exit_position(binance, symbol, position)
            op_mode = False

    # 9:00:20 ~ 9:00:30
    if now.hour == 9 and now.minute == 0 and (20 <= now.second < 30):
        target = cal_target(symbol)
        balance = binance.fetch_balance()
        usdt = balance['total']['USDT']
        post_message(myToken,"#autotrade",str(usdt)+"usdt : 오늘 내 자산")
        op_mode = True
        time.sleep(10)

    # 현재가 조회(1초마다)
    btc = binance.fetch_ticker(symbol)
    cur_price = btc['last']
    amount = cal_amount(usdt,cur_price)

    if op_mode and position['type'] is None:
        enter_position(binance, symbol,cur_price, target, amount, position)
       
        
    
   
    print(now, cur_price, target, position)
    time.sleep(1)

