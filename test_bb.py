import pandas as pd
import pandas_ta as ta
import requests

def get_binance_ohlcv(symbol, limit=100):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": "1h", "limit": limit}
    res = requests.get(url, params=params, timeout=10)
    data = res.json()
    df = pd.DataFrame(data, columns=[
        "time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "trades", "taker_buy_base", "taker_buy_quote", "ignore"
    ])
    df = df.astype({"open": float, "high": float, "low": float, "close": float, "volume": float})
    return df

df = get_binance_ohlcv("BTCUSDT", 100)
df.ta.bbands(append=True)
print(df.columns.tolist())
