import os
import time
import pandas as pd
from binance import Client

API_KEY = '13mt74xyCE5cD6Mhzw8B9Cvx2e0KsShKxarJAyDLQHB8nHxbeTZyaKZKXx9Dsby6'
SECRET_KEY = 'CDxaNtjTG6ckwATBkqfHRATtBkmHCjry6zKfMZYpMPjuVAWXFjETdzgmsPQkLiX2'

client = Client(API_KEY, SECRET_KEY)

symbol = 'DOGEUSDT'
timeframe = Client.KLINE_INTERVAL_1DAY
short_window = 50
long_window = 200

symbols = client.get_all_tickers()

def execute_trades():

    print('Retrieving historical market data...')
    # Retrieve historical market data
    klines = client.get_historical_klines(symbol, timeframe, f"{long_window} day ago UTC")
    df = pd.DataFrame(klines, columns=['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'num_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    df['close'] = pd.to_numeric(df['close'])

    # Calculate moving averages
    df['short_mavg'] = df['close'].rolling(window=short_window, min_periods=1).mean()
    df['long_mavg'] = df['close'].rolling(window=long_window, min_periods=1).mean()

    # Signal generation
    df['signal'] = 0
    df.loc[df['short_mavg'] > df['long_mavg'], 'signal'] = 1
    df.loc[df['short_mavg'] < df['long_mavg'], 'signal'] = -1

    # Execute orders
    position = 0
    for index, row in df.iterrows():
        if row['signal'] == 1 and position == 0:
            print(f"Buying {symbol} at {row['close']}")
            try:
                step_size = 0.00000001
                print(client.get_avg_price(symbol=symbol)['price'])
                min_notional_list = [f['minNotional'] for f in client.get_symbol_info(symbol)['filters'] if f['filterType'] == 'MIN_NOTIONAL']
                if min_notional_list:
                    min_notional = float(min_notional_list[0])
                    quantity = float(min_notional) / row['close']
                    filters = client.get_symbol_info(symbol)['filters']
                    lot_size_filter = next(filter(lambda f: f['filterType'] == 'LOT_SIZE', filters))
                    step_size = float(lot_size_filter['stepSize'])
                    quantity = round(quantity / step_size) * step_size

                    client.create_order(
                        symbol=symbol,
                        side=Client.SIDE_BUY,
                        type=Client.ORDER_TYPE_MARKET,
                        quantity=quantity,
                        newOrderRespType='FULL'
                )
                position = 1
                print(f"Bought {symbol} at {row['close']}")
            except Exception as e:
                print(f"Error: {e}")
        elif row['signal'] == -1 and position == 1:
            print(f"Selling {symbol} at {row['close']}")
            try:
                quantity = client.get_asset_balance(asset=symbol[:-4])
                quantity = float(quantity['free'])
                filters = client.get_symbol_info(symbol)['filters']
                lot_size_filter = next(filter(lambda f: f['filterType'] == 'LOT_SIZE', filters))
                step_size = float(lot_size_filter['stepSize'])
                quantity = round(quantity / step_size) * step_size
                client.create_order(
                    symbol=symbol,
                    side=Client.SIDE_SELL,
                    type=Client.ORDER_TYPE_MARKET,
                    quantity=quantity,
                    newOrderRespType='FULL'
                )
                position = 0
                print(f"Sold {symbol} at {row['close']}")
            except Exception as e:
                print(f"Error: {e}")

while True:
    execute_trades()
