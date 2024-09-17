import time
import datetime
import math
import http.client, urllib
from pybit.unified_trading import HTTP
import json
import traceback

#load api keys
rob_api_key = 'HS0mAS2lCCvc5YGhBx'
rob_secret = 'cb34UD2zInoIybZB8UeBEWoTErFdBtHt5eKl'

trailing = input("Enter custom trailing value: ")
target = input("Enter custom target value: ")

def trailingStops():
	#print("Checking trailing stop positions")
	global target
	bybitAPI = HTTP(
		testnet = False,
		api_key = rob_api_key,
		api_secret = rob_secret)
	#check if position is open and in which direction
	positions = bybitAPI.get_positions(category='linear', settleCoin='USDT')['result']['list']
	positionsOpen = len(positions)
	if positionsOpen == 1:
		#print("Open Position found. Getting timestamp:")
		time = bybitAPI.get_server_time()["result"]["timeSecond"]
		#print("Timestamp: ", time)
		sixHours = 21600
		hour = datetime.datetime.fromtimestamp(int(time)).strftime('%H')
		minute = datetime.datetime.fromtimestamp(int(time)).strftime('%M')
		#print("Hour: ", hour)
		#print("Minute: ", minute)
		utc_hour = int(hour) - 10
		pastTime = int(time) - sixHours
		pastTime = pastTime * 1000
		candles = bybitAPI.get_kline(
			category="linear",
			symbol="BTCUSDT",
			interval=240,
			start=pastTime)
		high = float(candles["result"]["list"][0][2])
		low = float(candles["result"]["list"][0][3])
		#print("High: ", high)
		#print("Low: ", low)
		side = positions[0]["side"]
		if side == "Sell":
			#print("Sell order detected, checking to move stop loss.")
			if low <= float(target):
				print("Target of sell order reached, moving stoploss.")
				trailing_stop_order = bybitAPI.set_trading_stop(
						category='linear',
						symbol="BTCUSDT",
						stopLoss=str(float(target) + float(trailing)),
						tpslMode='Full',
						tpOrderType='Market',
						slOrderType='Market',
						positionIdx=0
						)
				target = str(float(target) - float(trailing))
		elif side == "Buy":
			#print("Buy order detected, checking to move stop loss.")
			if high >= float(target):
				print("Target of buy order reached, moving stoploss.")
				trailing_stop_order = bybitAPI.set_trading_stop(
					category='linear',
					symbol="BTCUSDT",
					stopLoss=str(float(target) - float(trailing)),
					tpslMode='Full',
					tpOrderType='Market',
					slOrderType='Market',
					positionIdx=0
					)
				target = str(float(target) + float(trailing))


def init_setup(): #read value of last message on startup so that last message of previous session is not counted as a new message
	datastream = open("last_signal.txt", 'r', encoding='utf8') 
	chatlog = datastream.read()
	datastream.close()
	content = chatlog
	#load symbols with open positions from previous sessions
	return content

def messageUpdate(content): #update latest message and ensure it is a new message
	counter = 0
	while True:
		try:
			time.sleep(0.2)
			counter += 1
			datastream = open("last_signal.txt", 'r', encoding='utf8')
			chatlog = datastream.read()
			datastream.close()
			if chatlog != content:
				content = chatlog
				data_dict = json.loads(chatlog)
				print(data_dict)
				connectAPI('rob', data_dict, rob_api_key, rob_secret, 0.10, data_dict["direction"])
			if counter >= 100:
				counter = 0
				trailingStops()

		except:
			print(traceback.format_exc())
			quit()

def connectAPI(account, params, api_key, secret_key, risk, direction):
	#connect to api
	bybitAPI = HTTP(
		testnet = False,
		api_key = api_key,
		api_secret = secret_key)

	abandon = False
	print("Initiating trade process...")
	#check for positions
	positions = len(bybitAPI.get_positions(category='linear', settleCoin='USDT')['result']['list'])
	 
	if positions == 0:
		print("positions ok")
	#get account balance
		balance = bybitAPI.get_wallet_balance(accountType='UNIFIED', coin='USDT')
		available = balance['result']['list'][0]['coin'][0]['availableToWithdraw']
		print("Available Balance: ", available)
		in_positions = balance['result']['list'][0]['coin'][0]['totalPositionIM']
		totalBalance = float(available) + float(in_positions)

		#get coin price
		ticker = bybitAPI.get_tickers(category='linear', symbol="BTCUSDT")
		currentPrice = float(ticker['result']['list'][0]['lastPrice'])
		

		#get price diff
		price_diff = abs(float(params["price"]) - currentPrice)
		if currentPrice > float(params["price"]):
			params["stoploss"] = str(float(params["stoploss"]) + price_diff)
			params["profit"] = str(float(params["profit"]) + price_diff)
			params["price"] = str(float(params["price"]) + price_diff)
		else:
			params["stoploss"] = str(float(params["stoploss"]) - price_diff)
			params["profit"] = str(float(params["profit"]) - price_diff)
			params["price"] = str(float(params["price"]) - price_diff)

		#calculate risk
		fiatQuantity = ((risk * float(totalBalance)) / (abs(float(params["stoploss"]) - float(params["price"])))) * float(params["price"])
		print(f"Purchase amount: {fiatQuantity}")

		buffer = fiatQuantity * 0.02

		#calculating required leverage
		if positions == 0:
			leverage = math.ceil((fiatQuantity + buffer)/(float(available)/2))
		if positions == 1:
			leverage = math.ceil((fiatQuantity + buffer)/float(available))

		#calculating qantity
		inst_info = bybitAPI.get_instruments_info(category='linear', symbol="BTCUSDT")
		minOrderQty = inst_info['result']['list'][0]['lotSizeFilter']['minOrderQty']
		orderQty = float(fiatQuantity) / float(params["price"])
		if "." in str(minOrderQty):
			roundTo = len(str(minOrderQty).split(".")[1])
			orderQty = round(orderQty, roundTo)
		else:
			orderQty = math.floor(orderQty)
		if orderQty >= float(minOrderQty):	
			print("Minimum order quantity: pass")
			#checking maximum leverage is above used leverage
			maxlever = inst_info['result']['list'][0]['leverageFilter']['maxLeverage']
			if leverage < float(maxlever):
				print("Leverage: pass")
				#rounding all price figures to the instruments native figures
				if '.' in str(params["price"]):
					roundTo = len(str(params["price"]).split('.')[1])
					
				else:
					roundTo = 0

				#setting leverage
				try:
					bybitAPI.set_leverage(category='linear', symbol="BTCUSDT", buyLeverage=str(leverage), sellLeverage=str(leverage))
				except:
					x = 1
				trailing = str(round(abs(float(params["price"]) - float(params["profit"])), roundTo))
				
				#placing trade
				direction = direction.capitalize()
				init_order = bybitAPI.place_order(
					category='linear',
					symbol="BTCUSDT",
					side=direction,
					orderType='Limit',
					qty=str(orderQty),
					price=params["price"]
					)
				orderId = init_order["result"]["orderId"]
				print(init_order)
				new_position = "0"
				timer = 0
				while new_position == "0" and timer < 60:
					time.sleep(0.5)
					new_position = bybitAPI.get_positions(category='linear', symbol="BTCUSDT")['result']['list'][0]["avgPrice"]
					timer += 1
					if timer == 30:
						print(f"Trying for {timer} more seconds.")
				if timer >= 60:
					print("Trade aborted: Position not filled in time.")
					bybitAPI.cancel_order(category="linear", symbol="BTCUSDT", orderId=orderId)
				else:
					global target
					target = params["profit"]
					profit_order = bybitAPI.set_trading_stop(
						category='linear',
						symbol="BTCUSDT",
						takeProfit=params["profit"],
						tpslMode="Partial",
						tpSize=str(orderQty/2),
						slSize=str(orderQty/2),
						tpOrderType="Market",
						slOrderType="Market",
						positionIdx=0
					)

					trailing_stop_order = bybitAPI.set_trading_stop(
						category='linear',
						symbol="BTCUSDT",
						stopLoss=params["stoploss"],
						tpslMode='Full',
						tpOrderType='Market',
						slOrderType='Market',
						positionIdx=0
						)
	else:
		print("Position already open.")


content = init_setup()
print("Processor ready!")
messageUpdate(content)







